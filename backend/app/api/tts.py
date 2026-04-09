import base64
from fastapi import APIRouter, HTTPException
from app.schemas import TTSRequest, TTSResponse
from app.services.tts_service import synthesize_speech

router = APIRouter(prefix="/api/tts", tags=["tts"])

@router.post("", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    """
    Synthétise le texte en MP3 via edge-tts.
    
    Retourne le MP3 encodé en base64 — le frontend le joue directement
    avec un élément <audio> et une data URL :
    audio.src = `data:audio/mp3;base64,${response.audio_base64}`
    
    Note : endpoint async car edge-tts est entièrement async.
    FastAPI gère les endpoints async nativement — pas besoin d'asyncio.run().
    """
    try:
        audio_bytes, voice = await synthesize_speech(request.text, request.language)
        return TTSResponse(
            audio_base64=base64.b64encode(audio_bytes).decode(),
            voice_used=voice,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS échoué : {e}")
