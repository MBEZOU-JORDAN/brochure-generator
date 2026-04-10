from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api import search, brochure, tts, flyer

app = FastAPI(
    title="BrochureAI Pro",
    description="Génère des brochures professionnelles à partir d'une URL ou d'un nom d'entreprise",
    version="2.0.0",
    root_path="",
)

# ── CORS ───────────────────────────────────────────────────────────────────────
# CORS (Cross-Origin Resource Sharing) : permet au frontend (ex: localhost:5500)
# d'appeler le backend (localhost:8000) sans que le navigateur bloque la requête.
# En production : remplacer ["*"] par le domaine exact du frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://brochure-generator-six.vercel.app/", 
        "https://brochure-generator-six.vercel.app",
        "http://localhost:5500",
        "http://127.0.0.1:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(search.router)
app.include_router(brochure.router)
app.include_router(tts.router)
app.include_router(flyer.router)

# ── Healthcheck ────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}

@app.get("/")
async def root():
    return {"message": "Brochure Generator API is running!"}

# ── Dev server ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
