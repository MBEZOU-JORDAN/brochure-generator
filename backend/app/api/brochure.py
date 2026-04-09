import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.schemas.schemas import BrochureRequest
from app.services.web_search import search_company
from app.services.scraper import scrape_url, scrape_multiple
from app.services.llm_service import extract_relevant_links, generate_brochure_stream

router = APIRouter(prefix="/api/brochure", tags=["brochure"])


def _make_event(type_: str, **kwargs) -> str:
    """
    Formate un événement SSE.
    Format standard : "data: {json}\\n\\n"
    Le double \\n est obligatoire — c'est le délimiteur du protocole SSE.
    """
    payload = {"type": type_, **kwargs}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def _brochure_generator(request: BrochureRequest):
    """
    Générateur async qui orchestre tout le pipeline et yield des events SSE.
    
    Pipeline :
    1. Résoudre l'URL (recherche si absente)
    2. Scraper la page principale
    3. LLM extrait les liens pertinents
    4. Scraper les sous-pages
    5. Streamer la brochure token par token
    """

    # ── Étape 1 : Résoudre l'URL ───────────────────────────────────────────────
    url = request.url

    if not url:
        yield _make_event("status", message=f"🔍 Recherche de {request.company_name}...")
        try:
            results = search_company(request.company_name, max_results=3)
            if not results:
                yield _make_event("error", message="Aucun résultat trouvé. Vérifiez le nom.")
                return
            url = results[0].url
            yield _make_event("status", message=f"✓ Site trouvé : {url}")
        except Exception as e:
            yield _make_event("error", message=f"Erreur de recherche : {e}")
            return

    # ── Étape 2 : Scraper la page principale ──────────────────────────────────
    yield _make_event("status", message="📄 Analyse de la page principale...")
    try:
        main_page = scrape_url(url)
    except ValueError as e:
        yield _make_event("error", message=str(e))
        return

    # ── Étape 3 : Extraire les liens pertinents ────────────────────────────────
    yield _make_event("status", message="🤖 Identification des sections clés...")
    links_response = extract_relevant_links(url, main_page.links)
    relevant_urls = [item.url for item in links_response.links[:4]]

    if relevant_urls:
        yield _make_event("status", message=f"📑 {len(relevant_urls)} sections identifiées...")

    # ── Étape 4 : Scraper toutes les pages ────────────────────────────────────
    all_urls = [url] + relevant_urls
    yield _make_event("status", message=f"🔄 Extraction du contenu ({len(all_urls)} pages)...")
    aggregated = scrape_multiple(all_urls, max_chars_per_page=3000)

    # ── Étape 5 : Générer la brochure en streaming ────────────────────────────
    yield _make_event("status", message="✍️ Génération de la brochure...")
    yield _make_event("start")  # Signal au frontend : afficher la zone de résultat

    full_brochure = ""
    for token in generate_brochure_stream(request.company_name, aggregated):
        full_brochure += token
        yield _make_event("token", content=token)

    # ── Étape 6 : Signal de fin ────────────────────────────────────────────────
    yield _make_event("done", brochure=full_brochure, url=url)


@router.post("/stream")
async def stream_brochure(request: BrochureRequest):
    """
    Endpoint SSE — génère la brochure en streaming.
    
    Le frontend consomme ce flux via fetch() + ReadableStream (pas EventSource
    car EventSource ne supporte pas POST nativement).
    
    Headers importants :
    - Cache-Control: no-cache → désactive le cache pour le streaming
    - X-Accel-Buffering: no  → désactive le buffering nginx (crucial en prod)
    """
    return StreamingResponse(
        _brochure_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )
