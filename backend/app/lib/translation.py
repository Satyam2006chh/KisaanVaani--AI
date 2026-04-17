import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Uses Sarvam AI to translate text."""
    if not text or source_lang == target_lang:
        return text
    
    # Handle English-to-English edge case
    if source_lang.startswith("en") and target_lang.startswith("en"):
        return text

    if "your_sarvam_api_key" in settings.sarvam_api_key or not settings.sarvam_api_key:
        return f"[MOCK TRANSLATION to {target_lang}] {text}"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                "https://api.sarvam.ai/translate",
                headers={"api-subscription-key": settings.sarvam_api_key},
                json={
                    "input": text,
                    "source_language_code": source_lang,
                    "target_language_code": target_lang,
                    "model": "mayura:v1"
                }
            )
            r.raise_for_status()
            return r.json().get("translated_text", text)
    except Exception as e:
        logger.warning(f"Translation failed: {e}")
        return text
