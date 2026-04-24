# Voice Pipeline Debugging Guide

## Problem
User reports voice feature is stuck in "loading" (PROCESSING state) indefinitely after pressing the mic button.

## Root Cause Analysis
The voice pipeline has these failure points:
1. **Audio capture** - Microphone not working or permission denied
2. **Audio encoding** - FFmpeg conversion may fail without proper setup
3. **API communication** - Network timeout or backend not responding
4. **Sarvam STT** - API key invalid, rate limited, or audio format incompatible
5. **Agent processing** - LangGraph may be slow or erroring
6. **TTS playback** - Sarvam TTS failing or network issue

## Changes Made

### Frontend (React)
**File: `frontend/src/components/Hero/Hero.jsx`**
- Added `console.log` at every step (prefixed with `[VOICE]`)
- Added MediaRecorder error handler
- Added state logging in stopRecording()
- Changed `recorder.start()` to `recorder.start(100)` to request audio chunks every 100ms

**File: `frontend/src/api.js`**
- Added logging to `chatWithAgent()`, `speakText()`, `transcribeAudio()`
- Improved error logging to show status codes and response data
- Fixed transcribeAudio to properly handle FormData multipart requests

### Backend (Python/FastAPI)
**File: `backend/app/routers/voice.py`**
- Added detailed logging to `/api/voice/transcribe` endpoint
- Enhanced error messages with more context
- Improved `_to_wav()` function logging (shows conversion sizes, errors)
- Better handling of FileNotFoundError when FFmpeg is missing
- Added timeout detection in subprocess

## Quick Fix Checklist

### 1. Browser Console Logs
Open DevTools (F12) → Console → filter for `[VOICE]` or `[API]`
- [ ] See logs starting with `[VOICE] Starting recording...`?
- [ ] See `[VOICE] Recording stopped. Blob size: XXXX` with non-zero size?
- [ ] See `[API] transcribeAudio:` call?
- [ ] See response from transcribeAudio API?

### 2. Common Fixes

**If stuck at "Status set to PROCESSING":**
- Backend not responding (check Render logs)
- Network timeout (45s limit)
- API endpoint not being called

**If blob size is 0:**
```
[VOICE] Recording stopped. Blob size: 0 bytes
```
→ Audio not being captured:
- [ ] Check browser microphone permission
- [ ] Try Chrome instead of Safari/Firefox
- [ ] Try speaking louder/clearer
- [ ] Restart browser

**If transcription shows SILENCE_DETECTED:**
```
[VOICE] Transcription response: {status: "SILENCE_DETECTED"}
```
→ Audio too quiet or speech not detected:
- [ ] Speak louder and for 2-3 seconds minimum
- [ ] Check microphone levels in OS settings
- [ ] Use another device to test

**If API call fails:**
```
[API] transcribeAudio error: {status: 502}
```
→ Sarvam API or Render backend issue:
- [ ] Check Render logs: https://dashboard.render.com
- [ ] Verify SARVAM_API_KEY is set in Render environment
- [ ] Verify ffmpeg is installed (check apt.txt)
- [ ] Check if Sarvam API is down (https://status.sarvam.ai)

### 3. Backend Verification

Check Render logs for:
```
Transcribe request: language=hi-IN, filename=audio.webm
Processing audio: file=audio.webm, ext=webm, size=XXXX
FFmpeg conversion: XXXX -> YYYY bytes
Calling Sarvam STT API with YYYY bytes
Sarvam STT response: status=200
Sarvam Answer: 'Your text' [Detected: hi-IN]
```

If you see `ffmpeg error:` → FFmpeg is failing
If you see `Sarvam STT Failed:` → Sarvam API issue

## Manual Testing Steps

### Test 1: Frontend Audio Capture
```javascript
// In browser console:
navigator.mediaDevices.getUserMedia({audio: true})
  .then(stream => {
    const recorder = new MediaRecorder(stream)
    let chunks = []
    recorder.ondataavailable = e => chunks.push(e.data)
    recorder.start(100)
    console.log('Recording... speak now')
    setTimeout(() => {
      recorder.stop()
      const blob = new Blob(chunks, {type: 'audio/webm'})
      console.log('Blob size:', blob.size)
    }, 3000)
  })
  .catch(err => console.error('Mic error:', err))
```

### Test 2: Backend Transcription (curl)
```bash
# From your computer (not Render):
curl -X POST https://kisaanvaani-ai-1.onrender.com/api/voice/transcribe \
  -H "Content-Type: multipart/form-data" \
  -F "audio=@test_audio.wav" \
  -F "language=hi-IN"
```

### Test 3: Sarvam API Direct
```bash
# Test if Sarvam API key works:
curl -X POST https://api.sarvam.ai/speech-to-text \
  -H "api-subscription-key: YOUR_KEY_HERE" \
  -F "file=@test_audio.wav" \
  -F "language_code=hi-IN" \
  -F "model=saarika:v2.5"
```

## Solution Path

1. **Open browser console** and reproduce the issue
2. **Copy all [VOICE] and [API] logs**
3. **Identify which step fails** (using log sequences above)
4. **Apply specific fix** from checklist
5. **Test again** and monitor console

## Files Modified
- `frontend/src/components/Hero/Hero.jsx` - Recording and processing logic with logging
- `frontend/src/api.js` - API calls with detailed error logging
- `backend/app/routers/voice.py` - Transcription endpoint with comprehensive logging
- Added this file: `VOICE_DEBUGGING_GUIDE.md`

## What Changed in Code

### MediaRecorder now requests data every 100ms
```javascript
// Before:
recorder.start()

// After:
recorder.start(100)  // Request data every 100ms for safety
```
This ensures audio chunks are collected regularly, not just on stop.

### Better error context from backend
```python
# Before:
logger.error(f"Sarvam STT Failed: {e}")

# After:
logger.error(f"Sarvam STT Failed: {type(e).__name__}: {e}")
logger.info(f"Transcribe: original={len(audio_bytes)}B processed_wav={len(wav)}B")
```

### Frontend logs every API call
```javascript
console.log('[API] transcribeAudio:', { blobSize: blob.size, ext, language })
// ... call
console.log('[API] transcribeAudio response:', { status: data.status, ... })
```

## Environment Check

Make sure backend has:
- [ ] SARVAM_API_KEY set in Render environment
- [ ] ffmpeg installed (in apt.txt)
- [ ] Python packages installed (requirements.txt)
- [ ] All dependencies working

## Next Steps

1. Deploy changes to Netlify (push to git)
2. Test voice feature in browser
3. Open Console (F12)
4. Reproduce issue
5. Copy [VOICE] logs
6. Check Render logs
7. Share both log sets for analysis

