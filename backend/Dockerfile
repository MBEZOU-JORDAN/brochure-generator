FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Installation des dépendances système si nécessaire
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# On copie d'abord uniquement les fichiers de dépendances (cache Docker)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# On copie le reste du code
COPY . .

# On expose le port (Railway utilise souvent 8080 par défaut, ou via variable PORT)
EXPOSE 8000

# Commande de lancement (On utilise uv run pour l'environnement virtuel)
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]