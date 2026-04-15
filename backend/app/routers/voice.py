import base64
import io
import logging
import os
import subprocess
import tempfile

import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.config import settings
from app.models.schemas import TTSRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice", tags=["Voice"])

SARVAM_STT = "https://api.sarvam.ai/speech-to-text"
SARVAM_TTS = "https://api.sarvam.ai/text-to-speech"

SPEAKERS = {
    "hi-IN": "anushka", "pa-IN": "manisha", "bn-IN": "manisha",
    "ta-IN": "anushka", "te-IN": "anushka", "kn-IN": "anushka",
    "ml-IN": "anushka", "mr-IN": "manisha", "gu-IN": "manisha",
    "od-IN": "abhilash", "en-IN": "anushka",
}


def _to_wav(audio_bytes: bytes, ext: str) -> bytes:
    inp_path = out_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as f:
            f.write(audio_bytes)
            inp_path = f.name
        out_path = inp_path.replace(f".{ext}", "_out.wav")
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", inp_path, "-ar", "16000", "-ac", "1", "-sample_fmt", "s16", out_path],
            capture_output=True, timeout=30,
        )
        if result.returncode != 0:
            logger.warning(f"ffmpeg error: {result.stderr.decode()}")
            return audio_bytes
        with open(out_path, "rb") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("ffmpeg not found — sending raw audio")
        return audio_bytes
    except Exception as e:
        logger.warning(f"Audio conversion failed: {e}")
        return audio_bytes
    finally:
        for p in [inp_path, out_path]:
            if p:
                try:
                    os.unlink(p)
                except Exception:
                    pass


@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...), language: str = "hi-IN"):
    if not settings.sarvam_api_key:
        raise HTTPException(status_code=500, detail="Sarvam API key not configured")

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    fname = audio.filename or "audio.webm"
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else "webm"
    wav = _to_wav(audio_bytes, ext)
    logger.info(f"Transcribe: original={len(audio_bytes)}B  wav={len(wav)}B  lang={language}")

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            SARVAM_STT,
            headers={"api-subscription-key": settings.sarvam_api_key},
            files={"file": ("audio.wav", wav, "audio/wav")},
            data={"language_code": language, "model": "saarika:v2.5"},
        )

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Sarvam STT error: {r.text}")

    transcript = r.json().get("transcript", "").strip()
    logger.info(f"Transcript: '{transcript}'")
    return {"transcript": transcript, "language": language}


@router.post("/speak")
async def speak(req: TTSRequest):
    if not settings.sarvam_api_key:
        raise HTTPException(status_code=500, detail="Sarvam API key not configured")

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            SARVAM_TTS,
            headers={"api-subscription-key": settings.sarvam_api_key, "Content-Type": "application/json"},
            json={
                "inputs": [req.text],
                "target_language_code": req.language,
                "speaker": SPEAKERS.get(req.language, "anushka"),
                "enable_preprocessing": True,
                "model": "bulbul:v2",
            },
        )

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Sarvam TTS error: {r.text}")

    audio_bytes = base64.b64decode(r.json().get("audios", [""])[0])
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/wav")
