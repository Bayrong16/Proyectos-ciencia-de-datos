from fastapi import APIRouter, HTTPException

from app.models import (
    TranslationRequest,
    TranslationResponse,
)

from app.services import translate_text

# Crear el router
router = APIRouter()


@router.post(
    "/translate",
    response_model=TranslationResponse
)
async def translate(request: TranslationRequest):
    """
    Traduce un texto del inglés al español.
    """

    try:
        translated_text = translate_text(request.input_str)

        return TranslationResponse(
            translated_text=translated_text
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )