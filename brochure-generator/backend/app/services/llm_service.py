import json
from typing import Generator
from groq import Groq
from app.core.config import settings
from app.schemas.schemas import LinksResponse, LinkItem

client = Groq(api_key=settings.groq_api_key)

# Llama 3.3-70b : meilleur modèle gratuit disponible sur Groq en 2025
# ALTERNATIVE : llama-3.1-8b-instant → 10x plus rapide, qualité légèrement inférieure
# Trigger pour switcher : latence > 10s ou rate limit répété
MODEL_FAST = "llama-3.3-70b-versatile"
MODEL_LIGHT = "llama-3.1-8b-instant"

# ── Prompts système ────────────────────────────────────────────────────────────

LINK_SYSTEM_PROMPT = """Tu analyses des liens d'une page web pour créer une brochure d'entreprise.
Sélectionne uniquement les liens vers : About/À propos, Équipe, Produits/Services, Carrières, Contact, Presse.
Ignore : réseaux sociaux, CGU, cookies, PDF, connexion, panier, termes légaux.
RÉPONDS UNIQUEMENT en JSON valide, sans texte avant ni après, sans markdown.
Format exact :
{"links": [{"type": "about page", "url": "https://..."}, {"type": "products", "url": "https://..."}]}"""

BROCHURE_SYSTEM_PROMPT = """Tu es un expert en communication d'entreprise et marketing B2B.
Tu rédiges des brochures professionnelles structurées en Markdown, percutantes et claires.

Structure à respecter impérativement :
# [Nom de l'entreprise]
> [Tagline ou accroche percutante extraite du site]

## À propos
[2-3 paragraphes sur l'entreprise, sa mission, son histoire]

## Nos solutions
[Description des produits/services principaux, avec avantages clés]

## Pourquoi nous choisir
[3-5 points différenciants, en bullet points]

## Notre équipe / Culture
[Si info disponible sur le site]

## Nous rejoindre
[Si section carrières disponible]

## Contact & Coordonnées

---
Ton : professionnel, positif, orienté valeur client.
Adapte la langue à celle du site web source.
N'invente rien — base-toi uniquement sur le contenu fourni."""

FLYER_PROMPT_SYSTEM = """Tu génères des prompts de qualité pour la génération d'images avec FLUX.1.
À partir d'une brochure d'entreprise, génère un prompt pour créer un flyer professionnel.
Le prompt doit être en anglais, très détaillé visuellement.
Réponds UNIQUEMENT avec le prompt brut, sans introduction ni explication."""

# ── Fonctions ──────────────────────────────────────────────────────────────────

def extract_relevant_links(base_url: str, links: list[str]) -> LinksResponse:
    """
    Appel LLM léger (8b) pour filtrer les liens — tâche simple, pas besoin de 70b.
    Utilise le modèle rapide pour minimiser la latence sur cette étape intermédiaire.
    """
    links_text = "\n".join(links[:60])

    response = client.chat.completions.create(
        model=MODEL_LIGHT,
        messages=[
            {"role": "system", "content": LINK_SYSTEM_PROMPT},
            {"role": "user", "content": f"URL de base : {base_url}\n\nLiens :\n{links_text}"},
        ],
        temperature=0.05,  # Quasi-déterministe pour JSON stable
        max_tokens=600,
    )

    raw = response.choices[0].message.content.strip()

    # Nettoyage défensif : certains modèles wrappent dans ```json ... ```
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip().rstrip("`")

    try:
        data = json.loads(raw)
        return LinksResponse(**data)
    except Exception:
        return LinksResponse(links=[])  # Fallback propre — pas de crash


def generate_brochure_stream(
    company_name: str,
    aggregated_content: str,
) -> Generator[str, None, None]:
    """
    Génère la brochure en streaming SSE.
    
    Yield : chaque token du LLM au fur et à mesure.
    Le résultat cumulé est maintenu côté frontend via append.
    
    SSE format attendu par le frontend :
    data: {"type": "token", "content": "texte"}\\n\\n
    """
    user_prompt = (
        f"Crée une brochure complète pour : {company_name}\n\n"
        f"Contenu extrait du site :\n{aggregated_content[:10000]}"
    )

    stream = client.chat.completions.create(
        model=MODEL_FAST,
        messages=[
            {"role": "system", "content": BROCHURE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        stream=True,
        temperature=0.7,
        max_tokens=2000,
    )

    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield delta


def build_flyer_prompt(company_name: str, brochure_text: str, style: str) -> str:
    """
    Fait appel au LLM pour transformer la brochure en prompt visuel pour FLUX.1.
    Le LLM extrait : couleurs de marque, secteur, valeurs, pour un prompt cohérent.
    """
    style_hints = {
        "modern": "modern corporate design, clean lines, geometric shapes, professional",
        "elegant": "luxury elegant design, serif fonts implied, gold accents, premium feel",
        "bold": "bold graphic design, high contrast, strong typography, impactful",
        "minimal": "minimalist design, lots of white space, simple shapes, refined",
    }

    response = client.chat.completions.create(
        model=MODEL_LIGHT,
        messages=[
            {"role": "system", "content": FLYER_PROMPT_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Company: {company_name}\n"
                    f"Style direction: {style_hints.get(style, style_hints['modern'])}\n\n"
                    f"Brochure content (excerpt):\n{brochure_text[:2000]}\n\n"
                    "Generate a detailed image generation prompt for a professional marketing flyer."
                ),
            },
        ],
        temperature=0.8,
        max_tokens=300,
    )

    return response.choices[0].message.content.strip()
