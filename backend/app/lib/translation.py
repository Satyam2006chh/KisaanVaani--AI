import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Languages that Sarvam Translate supports
# (Assamese is supported in STT/TTS but translation may vary)
SARVAM_TRANSLATE_SUPPORTED = {
    "hi-IN", "pa-IN", "bn-IN", "ta-IN", "te-IN",
    "kn-IN", "ml-IN", "mr-IN", "gu-IN", "od-IN", "as-IN", "en-IN"
}

async def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """Uses Sarvam AI to translate text. Falls back gracefully."""
    if not text:
        return text
    if source_lang == target_lang:
        return text
    # English-to-English shortcut
    if source_lang.startswith("en") and target_lang.startswith("en"):
        return text

    if not settings.sarvam_api_key or "your_sarvam_api_key" in settings.sarvam_api_key:
        return text  # Return original if no key (no mock prefix to avoid garbling)

    # Skip translation if either lang is unsupported
    if source_lang not in SARVAM_TRANSLATE_SUPPORTED or target_lang not in SARVAM_TRANSLATE_SUPPORTED:
        logger.warning(f"Unsupported translation pair: {source_lang} → {target_lang}, returning original")
        return text

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.post(
                "https://api.sarvam.ai/translate",
                headers={"api-subscription-key": settings.sarvam_api_key},
                json={
                    "input": text,
                    "source_language_code": source_lang,
                    "target_language_code": target_lang,
                    "model": "mayura:v1",
                    "enable_preprocessing": False,
                }
            )
            if r.status_code == 200:
                return r.json().get("translated_text", text)
            else:
                logger.warning(f"Sarvam translate failed {r.status_code}: {r.text[:100]}")
                return text
    except Exception as e:
        logger.warning(f"Translation failed: {e}")
        return text
