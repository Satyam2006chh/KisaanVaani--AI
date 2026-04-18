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
from app.lib.translation import translate_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice", tags=["Voice"])

SARVAM_STT = "https://api.sarvam.ai/speech-to-text"
SARVAM_TTS = "https://api.sarvam.ai/text-to-speech"

SPEAKERS = {
    "hi-IN": "anushka", "pa-IN": "manisha", "bn-IN": "manisha",
    "ta-IN": "anushka", "te-IN": "anushka", "kn-IN": "anushka",
    "ml-IN": "anushka", "mr-IN": "manisha", "gu-IN": "manisha",
    "od-IN": "abhilash", "as-IN": "manisha", "en-IN": "anushka",
}

# Default message if nothing is heard
SILENCE_REPLY = {
    "hi-IN": "Maaf kijiye, mujhe aapki awaaz sunai nahi di. Kya aap phir se bol sakte hain?",
    "en-IN": "I'm sorry, I couldn't hear you. Could you please say that again?",
    "ta-IN": "மன்னிக்கவும், உங்கள் குரல் கேட்கவில்லை. தயவுசெய்து மீண்டும் சொல்ல முடியுமா?",
    "te-IN": "క్షమించండి, మీ వాయిస్ వినిపించలేదు. దయచేసి మళ్ళీ చెప్పగలరా?",
    "kn-IN": "ಕ್ಷಮಿಸಿ, ನಿಮ್ಮ ಧ್ವನಿ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಹೇಳಬಹುದೇ?",
    "ml-IN": "ക്ഷമിക്കണം, നിങ്ങളുടെ ശബ്ദം കേൾക്കാനായില്ല. ദയവായി വീണ്ടും പറയാമോ?",
    "mr-IN": "क्षमस्व, मला तुमचा आवाज ऐकू आला नाही. कृपया पुन्हा सांगू शकाल का?",
    "gu-IN": "ક્ષમા કરશો, મને તમારો અવાજ સંભળાયો નથી. શું તમે ફરીથી કહી શકશો?",
    "pa-IN": "ਮੁਆਫ ਕਰਨਾ, ਮੈਨੂੰ ਤੁਹਾਡੀ ਆਵਾਜ਼ ਸੁਣਾਈ ਨਹੀਂ ਦਿੱਤੀ। ਕੀ ਤੁਸੀਂ ਦੁਬਾਰਾ ਬੋਲ ਸਕਦੇ ਹੋ?",
    "bn-IN": "দুঃখিত, আমি আপনার কথা শুনতে পাইনি। আপনি কি আবার বলতে পারেন?",
    "od-IN": "କ୍ଷମା କରିବେ, ମୋତେ ଆପଣଙ୍କ ସ୍ୱର ଶୁଭିଲା ନାହିଁ । ଦୟାକରି ପୁଣିଥରେ କହିବେ କି?",
    "as-IN": "দুঃখিত, মই আপোনাৰ মাত শুনিবলৈ নাপালোঁ। আপুনি আকৌ ক’ব পাৰিবনে?",
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
    if "your_sarvam_api_key" in settings.sarvam_api_key or not settings.sarvam_api_key:
        print("WARNING: Using mock Sarvam STT response because SARVAM_API_KEY is not configured.")
        return {"transcript": "[MOCK TRANSCRIPT] Aap kaise hain?", "language": language}

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    fname = audio.filename or "audio.webm"
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else "webm"
    
    # Universal Conversion using FFmpeg (Handles OGG/WebM/MP3 to WAV)
    # This is the ONLY way to guarantee compatibility across WhatsApp/Mobile
    wav = _to_wav(audio_bytes, ext)
    
    if not wav or len(wav) < 1000:
        logger.warning("Audio processing failed or is too small")
        return {"transcript": "", "language": language, "error": "Silent audio"}

    logger.info(f"Transcribe: original={len(audio_bytes)}B processed_wav={len(wav)}B lang={language}")

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            r = await client.post(
                SARVAM_STT,
                headers={"api-subscription-key": settings.sarvam_api_key},
                files={"file": ("audio.wav", wav, "audio/wav")},
                data={"language_code": language, "model": "saarika:v2.5"},
            )
            r.raise_for_status()
            res_json = r.json()
            transcript = res_json.get("transcript", "").strip()
            detected_lang = res_json.get("language_code", language)
            
            logger.info(f"Sarvam Answer: '{transcript}' [Detected: {detected_lang}]")
            
            if not transcript:
                return {
                    "transcript": "", 
                    "english_transcript": "", 
                    "language": language, 
                    "detected_language": detected_lang,
                    "status": "SILENCE_DETECTED",
                    "silence_reply": SILENCE_REPLY.get(detected_lang, SILENCE_REPLY["en-IN"])
                }

            # Translate to English for Agent consumption using DETECTED language
            english_transcript = await translate_text(transcript, detected_lang, "en-IN")
            
            return {
                "transcript": transcript, 
                "english_transcript": english_transcript, 
                "language": language,
                "detected_language": detected_lang,
                "status": "SUCCESS"
            }
        except Exception as e:
            logger.error(f"Sarvam STT Failed: {e}")
            return {"transcript": "", "language": language, "error": str(e), "status": "ERROR"}


@router.post("/speak")
async def speak(req: TTSRequest):
    if "your_sarvam_api_key" in settings.sarvam_api_key or not settings.sarvam_api_key:
        print("WARNING: Using mock Sarvam TTS response because SARVAM_API_KEY is not configured.")
        # Return a tiny silent WAV (1sec of silence, 16kHz, mono)
        silent_wav = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
        return StreamingResponse(io.BytesIO(silent_wav), media_type="audio/wav")


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
