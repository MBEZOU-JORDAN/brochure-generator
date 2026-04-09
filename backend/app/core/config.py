from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Pydantic-settings charge automatiquement les variables depuis .env
    Avantage vs os.getenv : validation au démarrage, pas au runtime
    """
    groq_api_key: str
    hf_token: str
    tts_voice_fr: str = "fr-FR-DeniseNeural"
    tts_voice_en: str = "en-US-JennyNeural"

    # Config : lire depuis .env, insensible à la casse
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

# Singleton — importé depuis n'importe quel service
settings = Settings()
