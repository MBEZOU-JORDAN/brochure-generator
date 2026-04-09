import base64
import io
import httpx
from app.core.config import settings

# FLUX.1-schnell : modèle de génération d'images de Black Forest Labs (2024)
# C'est le modèle open-source le plus performant actuellement — supérieur à SD XL
# Disponible gratuitement via HF Inference API (rate limité)
#
# ALTERNATIVE 1 : FLUX.1-dev (même famille, plus de détails, plus lent)
# Trigger : si le client exige une qualité maximale, budget = 0
#
# ALTERNATIVE 2 : Pollinations.ai (https://image.pollinations.ai)
# Avantage : 100% gratuit, pas d'API key, CORS ouvert
# Inconvénient : moins stable que HF, résolution limitée
# Trigger : HF rate limit répété ou HF_TOKEN absent


HF_API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"


def generate_flyer_image(prompt: str) -> tuple[str, str]:
    """
    Génère une image de flyer via FLUX.1-schnell sur HF Inference API.
    
    Retourne : (base64_png, provider_used)
    
    Fallback automatique vers Pollinations.ai si HF échoue.
    """
    # Enrichir le prompt pour un résultat flyer/marketing
    full_prompt = (
        f"{prompt}, "
        "professional marketing flyer, high resolution, "
        "clean typography, commercial photography quality, 4k"
    )

    # Tentative 1 : HF FLUX.1-schnell
    try:
        return _generate_hf(full_prompt), "HF FLUX.1-schnell"
    except Exception as e:
        print(f"[image_service] HF échoué ({e}), fallback vers Pollinations.ai")

    # Tentative 2 : Pollinations.ai (gratuit, no-auth)
    try:
        return _generate_pollinations(full_prompt), "Pollinations.ai"
    except Exception as e:
        raise RuntimeError(f"Génération d'image échouée sur tous les providers : {e}")


def _generate_hf(prompt: str) -> str:
    """
    Appel à l'API HF Inference pour FLUX.1-schnell.
    Retourne le PNG en base64.
    """
    headers = {"Authorization": f"Bearer {settings.hf_token}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "width": 1024,
            "height": 1024,
            "num_inference_steps": 4,   # FLUX schnell = 1-4 steps suffisent
        },
    }

    with httpx.Client(timeout=60) as client:
        response = client.post(HF_API_URL, headers=headers, json=payload)

    if response.status_code == 503:
        raise RuntimeError("Modèle HF en cours de chargement (cold start)")
    if response.status_code == 429:
        raise RuntimeError("Rate limit HF atteint")
    response.raise_for_status()

    # HF retourne directement les bytes de l'image (pas de JSON)
    image_bytes = response.content
    return base64.b64encode(image_bytes).decode()


def _generate_pollinations(prompt: str) -> str:
    """
    Fallback via Pollinations.ai — aucune clé requise.
    Encode le prompt dans l'URL.
    """
    import urllib.parse
    encoded = urllib.parse.quote(prompt[:500])
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"

    with httpx.Client(timeout=60) as client:
        response = client.get(url)
    response.raise_for_status()

    return base64.b64encode(response.content).decode()
