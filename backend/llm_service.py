import os
import json
from groq import Groq
from typing import Generator
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

from models import LinksResponse

load_dotenv()

# -------------- Initialisation du models ----------------

# Groq avec ces API ultra rapide

MODEL = "llama-3.3-70b-versatile"
groq_api_key = os.getenv("GROQ_API_KEY")

def groq_clients():
    client = Groq(
        api_key=groq_api_key
    )
    return client

# Si Groq atteint ca limite on utilisera HF
def hf_client():
    client = InferenceClient(
        model="mistralai/Mistral-7B-Instruct-v0.3",
        token=os.getenv("HF_TOKEN")
    )
    return client

# Choix du llm par defaut celui degroq
client = groq_clients()

# -------- PROMPTS SYSTEMS --------------
 
LINK_SYSTEM_PROMPT = """Tu es un assistant qui analyse les liens d'une page web.
Ton rôle : identifier les liens les plus pertinents pour créer une brochure d'entreprise.
Liens pertinents : About, À propos, Équipe, Carrières, Produits, Services, Contact.
Exclure : réseaux sociaux externes, CGU, cookies, liens techniques.

IMPORTANT : Réponds UNIQUEMENT avec du JSON valide, sans texte avant ou après.
Format exact :
{
  "links": [
    {"type": "about page", "url": "https://example.com/about"},
    {"type": "careers page", "url": "https://example.com/careers"}
  ]
}"""

BROCHURE_SYSTEM_PROMPT = """Tu es un expert en marketing et communication d'entreprise.
Tu crées des brochures professionnelles, structurées et convaincantes en Markdown.

Structure obligatoire :
# [Nom de l'entreprise]
## À propos
## Nos produits / services  
## Pourquoi nous choisir
## Nous rejoindre (si info dispo)
## Contact

Ton : professionnel, positif, orienté client.
Langue : adapter à la langue du site web."""


def extract_relevant_links(base_url: str, links: list[str]) -> LinksResponse:
    """
    Utilise le LLM pour filtrer les liens pertinents pour la brochure.
    Retourne un LinksResponse validé par Pydantic — jamais de crash JSON.
    """
    links_text = "\n".join(links[:50])  # Max 50 liens pour éviter overflow

    user_prompt = f"""URL de base : {base_url}

Liste des liens trouvés :
{links_text}

Sélectionne les liens pertinents pour une brochure d'entreprise."""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": LINK_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,  # Bas pour des sorties JSON stables
        max_tokens=500,
    )

    raw_json = response.choices[0].message.content.strip()

    # Nettoyage robuste — certains modèles ajoutent des ```json ... ```
    if raw_json.startswith("```"):
        raw_json = raw_json.split("```")[1]
        if raw_json.startswith("json"):
            raw_json = raw_json[4:]

    try:
        data = json.loads(raw_json)
        return LinksResponse(**data)
    except (json.JSONDecodeError, Exception):
        # Fallback : retourner liste vide plutôt que crash
        return LinksResponse(links=[])


def generate_brochure_stream(
    company_name: str,
    aggregated_content: str,
) -> Generator[str, None, None]:
    """
    Génère la brochure en streaming — l'utilisateur voit le texte s'écrire token par token.
    Retourne un générateur Python (yield).
    """
    user_prompt = f"""Crée une brochure professionnelle pour l'entreprise : {company_name}

Voici le contenu extrait de leur site web :
{aggregated_content[:8000]}"""

    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": BROCHURE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
        temperature=0.5,
        max_tokens=1500,
    )

    result = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        result += delta
        yield result  # Gradio reçoit l'état complet à chaque token