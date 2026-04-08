from pydantic import BaseModel
from typing import List

class LinkItem(BaseModel):
    """
    Représente un lien pertinent extrait d'une page web.
    type : catégorie du lien (ex: "about page", "careers")
    url  : URL complète et absolue
    """
    type: str
    url: str

class LinksResponse(BaseModel):
    """
    Réponse structurée du LLM pour l'extraction de liens.
    Pydantic garantit que le JSON est valide — pas de crash.
    """
    links: List[LinkItem]