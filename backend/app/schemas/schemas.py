from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional

# ── Recherche web ──────────────────────────────────────────────────────────────

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str

class SearchResponse(BaseModel):
    results: list[SearchResult]

# ── Extraction de liens ────────────────────────────────────────────────────────

class LinkItem(BaseModel):
    """Un lien pertinent extrait d'une page web par le LLM"""
    type: str          # "about page", "careers", "products"...
    url: str

class LinksResponse(BaseModel):
    """Réponse structurée du LLM — garantit un JSON valide même si le modèle hallucine"""
    links: list[LinkItem]

# ── Génération de brochure ─────────────────────────────────────────────────────

class BrochureRequest(BaseModel):
    company_name: str
    url: Optional[str] = None   # Si None → on utilise la recherche web

    @field_validator("company_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Le nom de l'entreprise est requis")
        return v.strip()

    @field_validator("url")
    @classmethod
    def normalize_url(cls, v: Optional[str]) -> Optional[str]:
        if v and not v.startswith("http"):
            return "https://" + v
        return v

# ── Synthèse vocale ────────────────────────────────────────────────────────────

class TTSRequest(BaseModel):
    text: str
    language: str = "fr"        # "fr" ou "en"

class TTSResponse(BaseModel):
    audio_base64: str           # MP3 encodé en base64
    voice_used: str

# ── Génération de flyer ────────────────────────────────────────────────────────

class FlyerRequest(BaseModel):
    brochure_text: str          # Le markdown de la brochure complète
    company_name: str
    style: str = "modern"       # "modern" | "elegant" | "bold" | "minimal"

class FlyerResponse(BaseModel):
    image_base64: str           # PNG encodé en base64
    prompt_used: str            # Pour debug et portfolio

# ── SSE Events (streaming brochure) ───────────────────────────────────────────
# Ces modèles ne sont pas envoyés comme body mais sérialisés en JSON dans les data SSE

class SSEEvent(BaseModel):
    type: str   # "status" | "token" | "done" | "error"
    content: Optional[str] = None   # token de texte
    message: Optional[str] = None   # message de statut
