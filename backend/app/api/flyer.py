from fastapi import APIRouter, HTTPException
from app.schemas.schemas import FlyerRequest, FlyerResponse
from app.services.llm_service import build_flyer_prompt
from app.services.image_service import generate_flyer_image

router = APIRouter(prefix="/api/flyer", tags=["flyer"])

@router.post("", response_model=FlyerResponse)
def generate_flyer(request: FlyerRequest):
    """
    Pipeline en 2 étapes :
    1. LLM transforme la brochure markdown → prompt visuel pour FLUX.1
    2. FLUX.1-schnell génère l'image (1024×1024)
    
    Retourne le PNG en base64 pour affichage direct dans <img> :
    img.src = `data:image/png;base64,${response.image_base64}`
    """
    try:
        # Étape 1 : Construire le prompt visuel
        visual_prompt = build_flyer_prompt(
            request.company_name,
            request.brochure_text,
            request.style,
        )

        # Étape 2 : Générer l'image
        image_b64, provider = generate_flyer_image(visual_prompt)

        return FlyerResponse(
            image_base64=image_b64,
            prompt_used=f"[{provider}] {visual_prompt}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
