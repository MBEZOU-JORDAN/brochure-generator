import asyncio
import edge_tts
from app.core.config import settings

# Mapping langue → voix neurales Microsoft
# edge-tts utilise le moteur TTS de Microsoft Edge — qualité production, zéro coût
# Liste complète : uv run edge-tts --list-voices
VOICE_MAP = {
    "fr": settings.tts_voice_fr,       # fr-FR-DeniseNeural (par défaut)
    "en": settings.tts_voice_en,       # en-US-JennyNeural (par défaut)
    "de": "de-DE-KatjaNeural",
    "es": "es-ES-ElviraNeural",
}

# ALTERNATIVE : ElevenLabs API (elevenlabs.io)
# Avantage : qualité supérieure, voix customisables, clonage de voix
# Inconvénient : 10k chars/mois en free tier, payant au-delà
# Trigger pour switcher : client exige voix custom ou qualité broadcast


async def synthesize_speech(text: str, language: str = "fr") -> tuple[bytes, str]:
    """
    Convertit un texte en MP3 via edge-tts.
    
    Retourne : (audio_bytes, voice_name)
    
    edge-tts est entièrement async — on utilise asyncio.run() uniquement
    si appelé depuis du code synchrone. Dans FastAPI async, on fait juste await.
    
    Limite pratique : textes très longs (>5000 chars) → chunker en paragraphes.
    Pour une brochure complète, prendre uniquement le résumé ou les sections clés.
    """
    voice = VOICE_MAP.get(language, VOICE_MAP["fr"])

    # Tronquer à 4000 chars pour éviter les timeouts — assez pour une brochure
    text_clean = text[:4000].strip()

    communicate = edge_tts.Communicate(text_clean, voice)

    audio_chunks: list[bytes] = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])

    audio_bytes = b"".join(audio_chunks)

    if not audio_bytes:
        raise RuntimeError("edge-tts n'a retourné aucune donnée audio")

    return audio_bytes, voice
