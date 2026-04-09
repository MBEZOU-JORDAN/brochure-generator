FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Dépendances
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Code
COPY . .

# IMPORTANT : HF Spaces utilise le port 7860 par défaut
ENV PORT=7860
EXPOSE 7860

# Lancement
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]