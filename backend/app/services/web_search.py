import asyncio
from duckduckgo_search import DDGS
from app.schemas.schemas import SearchResult

async def search_company(query: str, max_results: int = 6) -> list[SearchResult]:
    """
    Recherche web via DuckDuckGo — zéro API key, zéro coût.
    
    Stratégie : on cherche "[company] official website" pour maximiser la chance
    d'obtenir l'URL officielle en premier résultat.
    
    ALTERNATIVE : Tavily API (tavily.com) — 1000 recherches/mois gratuit,
    meilleure qualité pour les agents AI. Trigger : si DDG bloque (rate limit
    ou résultats vides répétés). Avantage : conçu pour les LLM pipelines.
    """
    # On définit une fonction interne synchrone pour DDGS
    def sync_search():
        enriched_query = f"{query} official website"
        try:
            with DDGS() as ddgs:
                return list(ddgs.text(enriched_query, max_results=max_results))
        except Exception as e:
            print(f"Erreur DDG: {e}")
            return []

    # On lance la recherche dans un thread séparé pour ne pas bloquer l'async
    raw_results = await asyncio.to_thread(sync_search)
    
    # Filtrer les résultats non-pertinents (Wikipedia, réseaux sociaux)
    skip_domains = {"wikipedia.org", "facebook.com", "linkedin.com", "twitter.com", "x.com"}
    
    results = []
    for r in raw_results:
        url = r.get("href", "")
        if any(domain in url for domain in skip_domains):
            continue
        results.append(SearchResult(
            title=r.get("title", ""),
            url=url,
            snippet=r.get("body", "")[:200],
        ))
    
    return results[:5]  # Max 5 résultats propres
