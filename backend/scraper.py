import httpx
from bs4 import BeautifulSoup
from typing import Optional

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

class Website:
    def __init__(self, url: str):
        self.url = url
        self.title = ""
        self.text = ""
        self.links: list[str] = []
        self._fetch()
        
    def _fetch(self):
        try:
            response = httpx.get(self.url, headers=HEADERS, timeout=15, follow_redirects=True)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise ValueError(f"Impossible de charger la page {self.url} : {e}")
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        self.title = soup.title.string.strip() if soup.title else "Sans titre"
        
        # Supprimer les elements non-textuels
        for tag in soup(["script", "style", "img", "input", "nav", "footer"]):
            tag.decompose()
            
        self.text = soup.get_text(separator="\n", strip=True) if soup.body else ""
        
        # Extraire les liens ansolus uniquement
        raw_links = [a.get("href") for a in soup.find_all("a") if a.get("href")]
        self.links = [
            link for link in raw_links
            if link.startswith("http") and len(link) < 200
        ]
        
    def get_contents(self) -> str:
        # Tronquer a 500 chars pour ne pas depasser le context window
        truncated = self.text[:5000]
        return f"**Titre:** {self.titre} \n\n**Contenu:**\n{truncated}" 

def scrape_multiple(urls: list[str]) -> str:
    """
    Scrape plusieurs URLs et agrege leur contenu.
    Utilise pour combiner page principale + sous-pages (about, careers...)
    """
    combined = ""
    for url in urls:
        try:
            site = Website(url)
            combined += f"\n\n---\n## Source: {url}\n{site.get_contents()}"
        except Exception as e:
            combined += f"\n\n## Source: {url}\n[Erreur: {e}]"
    return combined