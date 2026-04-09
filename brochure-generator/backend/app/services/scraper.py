import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

# Tags à supprimer — tout ce qui n'est pas du contenu textuel utile
NOISE_TAGS = ["script", "style", "img", "input", "button", "nav", "footer",
              "header", "aside", "form", "noscript", "iframe", "svg"]

class ScrapedPage:
    """Représente une page web scrapée et nettoyée"""

    def __init__(self, url: str, title: str, text: str, links: list[str]):
        self.url = url
        self.title = title
        self.text = text
        self.links = links

    def get_contents(self, max_chars: int = 4000) -> str:
        """
        Retourne le contenu formaté, tronqué à max_chars.
        On tronque ici (pas au niveau LLM) pour contrôler le coût en tokens.
        """
        return f"## Source : {self.url}\n**Titre :** {self.title}\n\n{self.text[:max_chars]}"


def scrape_url(url: str) -> ScrapedPage:
    """
    Scrape une URL de façon synchrone.
    
    httpx vs requests : httpx supporte HTTP/2 nativement, meilleure gestion
    des timeouts, et la même API s'utilise en async avec `async with httpx.AsyncClient()`.
    C'est l'outil de référence pour FastAPI.
    """
    try:
        with httpx.Client(headers=HEADERS, timeout=15, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
    except httpx.TimeoutException:
        raise ValueError(f"Timeout sur {url}")
    except httpx.HTTPStatusError as e:
        raise ValueError(f"HTTP {e.response.status_code} sur {url}")
    except Exception as e:
        raise ValueError(f"Impossible de charger {url} : {e}")

    soup = BeautifulSoup(response.content, "html.parser")

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # Nettoyer le DOM
    for tag in soup(NOISE_TAGS):
        tag.decompose()

    text = ""
    if soup.body:
        # separator="\n" pour garder la structure paragraphes
        text = soup.body.get_text(separator="\n", strip=True)
        # Réduire les lignes vides multiples
        lines = [l for l in text.splitlines() if l.strip()]
        text = "\n".join(lines)

    # Extraire les liens absolus uniquement
    raw_links = [a.get("href", "") for a in soup.find_all("a")]
    links = [
        l for l in raw_links
        if l.startswith("http") and len(l) < 300
    ]

    return ScrapedPage(url=url, title=title, text=text, links=links)


def scrape_multiple(urls: list[str], max_chars_per_page: int = 3000) -> str:
    """
    Scrape plusieurs URLs et agrège le contenu.
    Les erreurs par page ne font pas planter l'ensemble.
    """
    parts = []
    for url in urls:
        try:
            page = scrape_url(url)
            parts.append(page.get_contents(max_chars=max_chars_per_page))
        except ValueError as e:
            parts.append(f"## Source : {url}\n[Erreur: {e}]")
    return "\n\n---\n\n".join(parts)
