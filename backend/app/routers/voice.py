import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from app.config import settings
from app.models.schemas import TTSRequest
import io

router = APIRouter(prefix="/api/voice", tags=["Voice"])

SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"
SARVAM_TTS_URL = "https://api.sarvam.ai/text-to-speech"

# ─── Speech → Text ────────────────────────────────────────────
@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = "hi-IN"
):
    """
    Accepts audio file from React (WebM/WAV),
    sends to Sarvam AI STT, returns Hindi/Punjabi transcript.
    """
    audio_bytes = await audio.read()

    headers = {"api-subscription-key": settings.sarvam_api_key}

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            SARVAM_STT_URL,
            headers=headers,
            files={"file": (audio.filename or "audio.webm", audio_bytes, "audio/webm")},
            data={"language_code": language, "model": "saarika:v2"},
        )

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Sarvam STT error: {response.text}")

    data = response.json()
    return {"transcript": data.get("transcript", ""), "language": language}


# ─── Text → Speech ────────────────────────────────────────────
@router.post("/speak")
async def text_to_speech(req: TTSRequest):
    """
    Accepts Hindi/Punjabi text, returns MP3 audio stream from Sarvam TTS.
    """
    headers = {
        "api-subscription-key": settings.sarvam_api_key,
        "Content-Type": "application/json",
    }

    # Map language code to Sarvam speaker voice
    speakers = {
        "hi-IN": "meera",
        "pa-IN": "pavithra",
        "bn-IN": "bani",
        "ta-IN": "siya",
        "te-IN": "anushka",
        "kn-IN": "tara",
        "ml-IN": "dilasha",
        "mr-IN": "maitreyi",
        "gu-IN": "disha",
        "od-IN": "arjun",
        "en-IN": "maya",
    }
    speaker = speakers.get(req.language, "meera")

    payload = {
        "inputs": [req.text],
        "target_language_code": req.language,
        "speaker": speaker,
        "enable_preprocessing": True,
        "model": "bulbul:v1",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(SARVAM_TTS_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Sarvam TTS error: {response.text}")

    data = response.json()
    # Sarvam returns base64 encoded audio
    import base64
    audio_b64 = data.get("audios", [""])[0]
    audio_bytes = base64.b64decode(audio_b64)

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/wav",
        headers={"Content-Disposition": "inline; filename=response.wav"}
    )
