# BrochureAI Pro

Génère des brochures professionnelles, synthèses vocales et flyers marketing à partir de l'URL ou du nom d'une entreprise.

## Stack

| Couche | Technologie |
|---|---|
| Backend | FastAPI · Python 3.11+ · uv |
| LLM | Groq API — Llama 3.3-70b / 3.1-8b |
| Scraping | httpx · BeautifulSoup4 |
| Recherche web | DuckDuckGo Search (sans API key) |
| Synthèse vocale | edge-tts — voix neurales Microsoft |
| Génération image | HF FLUX.1-schnell · fallback Pollinations.ai |
| Frontend | HTML / CSS / JS vanilla |

## Prérequis

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) installé
- Clés API : `GROQ_API_KEY` · `HF_TOKEN`

## Installation

```bash
git clone https://github.com/ton-username/brochure-pro
cd brochure-pro/backend

cp .env.example .env
# Renseigner GROQ_API_KEY et HF_TOKEN dans .env

uv sync
```

## Lancer le projet

```bash
# Backend
cd backend
uv run uvicorn app.main:app --reload --port 8000

# Frontend — dans un second terminal
cd frontend
python3 -m http.server 5500
# → http://localhost:5500
```

## Docker

```bash
docker compose up --build
# Backend  → http://localhost:8000
# Frontend → http://localhost:5500
# Docs API → http://localhost:8000/docs
```

## Endpoints

| Méthode | Route | Description |
|---|---|---|
| GET | `/api/search?q=` | Recherche web DDG |
| POST | `/api/brochure/stream` | Génération brochure (SSE) |
| POST | `/api/tts` | Synthèse vocale MP3 |
| POST | `/api/flyer` | Flyer image FLUX.1 |
| GET | `/health` | Healthcheck |

## Structure

```
brochure-pro/
├── DESIGN.md
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── schemas.py
│       ├── api/        # search · brochure · tts · flyer
│       └── services/       # web_search · scraper · llm · tts · image
└── frontend/
    ├── Dockerfile
    ├── index.html
    ├── css/style.css
    └── js/               # api.js · app.js
```

## Variables d'environnement

| Variable | Obligatoire | Valeur par défaut |
|---|---|---|
| `GROQ_API_KEY` | ✅ | — |
| `HF_TOKEN` | ✅ | — |
| `TTS_VOICE_FR` | ❌ | `fr-FR-DeniseNeural` |
| `TTS_VOICE_EN` | ❌ | `en-US-JennyNeural` |

## Licence

MIT