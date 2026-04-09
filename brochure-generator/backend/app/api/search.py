from fastapi import APIRouter, HTTPException, Query
from app.schemas.schemas import SearchResponse
from app.services.web_search import search_company

router = APIRouter(prefix="/api/search", tags=["search"])

@router.get("", response_model=SearchResponse)
def search(q: str = Query(..., min_length=2, description="Nom de l'entreprise à rechercher")):
    """
    Recherche le site web d'une entreprise via DuckDuckGo.
    Utilisé quand l'utilisateur ne connaît pas l'URL exacte.
    """
    try:
        results = search_company(q)
        return SearchResponse(results=results)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
