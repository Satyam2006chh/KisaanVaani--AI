import base64
import io
import logging
import os
import subprocess
import tempfile

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.config import settings
from app.models.schemas import TTSRequest
from app.lib.translation import translate_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/voice", tags=["Voice"])

SARVAM_STT = "https://api.sarvam.ai/speech-to-text"
SARVAM_TTS = "https://api.sarvam.ai/text-to-speech"

# Unified Speakers for Bulbul v2 (Manisha is high-quality multi-lingual)
SPEAKERS = {
    "hi-IN": "manisha", "pa-IN": "manisha", "bn-IN": "manisha",
    "ta-IN": "manisha", "te-IN": "manisha", "kn-IN": "manisha",
    "ml-IN": "manisha", "mr-IN": "manisha", "gu-IN": "manisha",
    "od-IN": "manisha", "as-IN": "manisha", "en-IN": "manisha",
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
         # Optimized command for speed and Sarvam compatibility
        cmd = [
            "ffmpeg", "-y", "-i", inp_path,
            "-ar", "16000", "-ac", "1", "-sample_fmt", "s16",
            "-preset", "ultrafast", out_path
        ]
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
        )
        if result.returncode != 0:
            stderr = result.stderr.decode() if result.stderr else "unknown error"
            logger.error(f"FFmpeg error: {stderr}")
            return audio_bytes
        with open(out_path, "rb") as f:
            wav_data = f.read()
            logger.info(f"FFmpeg success: {len(audio_bytes)}B -> {len(wav_data)}B (WAV)")
            return wav_data
    except FileNotFoundError:
        logger.warning("ffmpeg not found — sending raw audio (install ffmpeg for better compatibility)")
        return audio_bytes
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg timeout - audio too large or slow system")
        return audio_bytes
    except Exception as e:
        logger.error(f"Audio conversion failed: {type(e).__name__}: {e}")
        return audio_bytes
    finally:
        for p in [inp_path, out_path]:
            if p:
                try:
                    os.unlink(p)
                except Exception:
                    pass


@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...), language: str = Form("hi-IN")):
    logger.info(f"Transcribe request: language={language}, filename={audio.filename}, content_type={audio.content_type}")
    
    if "your_sarvam_api_key" in settings.sarvam_api_key or not settings.sarvam_api_key:
        print("WARNING: Using mock Sarvam STT response because SARVAM_API_KEY is not configured.")
        transcript = "[MOCK TRANSCRIPT] Aap kaise hain?"
        return {
            "transcript": transcript,
            "english_transcript": transcript,
            "language": language,
            "detected_language": language,
            "status": "SUCCESS",
        }

    try:
        audio_bytes = await audio.read()
    except Exception as e:
        logger.error(f"Failed to read audio: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to read audio: {str(e)}")
    
    if not audio_bytes:
        logger.error("Empty audio file received")
        raise HTTPException(status_code=400, detail="Empty audio file")

    fname = audio.filename or "audio.webm"
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else "webm"
    
    logger.info(f"Processing audio: file={fname}, ext={ext}, size={len(audio_bytes)}")
    
    # Universal Conversion using FFmpeg (Handles OGG/WebM/MP3 to WAV)
    # This is the ONLY way to guarantee compatibility across WhatsApp/Mobile
    wav = _to_wav(audio_bytes, ext)
    
    if not wav or len(wav) < 1000:
        logger.warning(f"Audio processing failed or too small: wav_size={len(wav) if wav else 0}")
        return {
            "transcript": "",
            "english_transcript": "",
            "language": language,
            "detected_language": language,
            "status": "SILENCE_DETECTED",
            "silence_reply": SILENCE_REPLY.get(language, SILENCE_REPLY["en-IN"]),
            "error": "Silent or invalid audio",
        }

    logger.info(f"Transcribe: original={len(audio_bytes)}B processed_wav={len(wav)}B lang={language}")

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            logger.info(f"Calling Sarvam STT API with {len(wav)} bytes")
            r = await client.post(
                SARVAM_STT,
                headers={"api-subscription-key": settings.sarvam_api_key},
                files={"file": ("audio.wav", wav, "audio/wav")},
                data={"language_code": language, "model": "saarika:v2.5"},
            )
            logger.info(f"Sarvam STT response: status={r.status_code}")
            
            if r.status_code != 200:
                err_body = r.text
                logger.error(f"Sarvam STT Error {r.status_code}: {err_body}")
                if r.status_code == 401:
                    raise HTTPException(status_code=401, detail="Invalid Sarvam API Key. Please check .env")
                raise HTTPException(status_code=502, detail=f"Sarvam STT failed ({r.status_code})")
            
            res_json = r.json()
            transcript = res_json.get("transcript", "").strip()
            detected_lang = res_json.get("language_code", language)
            
            logger.info(f"Sarvam Answer: '{transcript}' [Detected: {detected_lang}]")
            
            if not transcript:
                logger.warning("Empty transcript from Sarvam")
                return {
                    "transcript": "", 
                    "english_transcript": "", 
                    "language": language, 
                    "detected_language": detected_lang,
                    "status": "SILENCE_DETECTED",
                    "silence_reply": SILENCE_REPLY.get(detected_lang, SILENCE_REPLY["en-IN"])
                }

            # Translate to English for Agent consumption using DETECTED language
            logger.info(f"Translating '{transcript}' from {detected_lang} to en-IN")
            english_transcript = await translate_text(transcript, detected_lang, "en-IN")
            
            return {
                "transcript": transcript, 
                "english_transcript": english_transcript, 
                "language": language,
                "detected_language": detected_lang,
                "status": "SUCCESS"
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Sarvam STT Failed: {type(e).__name__}: {e}")
        return {
            "transcript": "", 
            "english_transcript": "",
            "language": language, 
            "status": "ERROR", 
            "error": f"STT failed: {str(e)}"
        }


@router.post("/speak")
async def speak(req: TTSRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="Text required for speech")

    if "your_sarvam_api_key" in settings.sarvam_api_key or not settings.sarvam_api_key:
        print("WARNING: Using mock Sarvam TTS response because SARVAM_API_KEY is not configured.")
        # Return a tiny silent WAV (1sec of silence, 16kHz, mono)
        silent_wav = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
        return StreamingResponse(io.BytesIO(silent_wav), media_type="audio/wav")


    # Chunk text to avoid Sarvam's length limits (~500 chars)
    text = req.text
    max_chunk = 500
    chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                SARVAM_TTS,
                headers={"api-subscription-key": settings.sarvam_api_key, "Content-Type": "application/json"},
                json={
                    "inputs": chunks,
                    "target_language_code": req.language,
                    "speaker": req.speaker or SPEAKERS.get(req.language, "anushka"),
                    "enable_preprocessing": True,
                    "model": "bulbul:v2",
                },
            )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Sarvam TTS request failed: {str(e)}")

    if r.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Sarvam TTS error: {r.text}")

    audio_bytes = base64.b64decode(r.json().get("audios", [""])[0])
    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/wav")
