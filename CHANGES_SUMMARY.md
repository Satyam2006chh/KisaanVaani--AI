# Voice Feature Debug - Changes Summary

## Issue
Voice feature is stuck in loading state (PROCESSING) indefinitely. User speaks into mic, presses stop, but gets no response and remains in "AI soch raha hai" (AI thinking) loading state.

## Root Causes to Investigate
1. Audio blob might be empty (mic not capturing)
2. Audio transcription API (Sarvam STT) timing out or failing
3. Agent processing taking too long (>45s timeout)
4. FFmpeg not converting audio properly
5. Network issues between frontend and backend
6. Sarvam API key issue or rate limiting

## Changes Made

### 1. Frontend Logging (React)
**File: `frontend/src/components/Hero/Hero.jsx`**

#### Added comprehensive console logs:
- `[VOICE] Starting recording...` when mic button clicked
- `[VOICE] Requesting microphone access...` before getUserMedia
- `[VOICE] Microphone stream acquired` after successful stream
- `[VOICE] Recording started - awaiting stop signal` when recorder starts
- `[VOICE] Stop signal sent to MediaRecorder` when user clicks stop
- `[VOICE] Recording stopped. Blob size: XXXX bytes` after recording ends
- `[VOICE] Status set to PROCESSING...` when processing starts
- `[VOICE] Calling transcribeAudio with language: hi-IN` before API call
- `[VOICE] Transcription response:` showing response data
- And more for each step of agent/TTS

#### Enhanced error handling:
- Added `recorder.onerror` handler to catch recording errors
- Added `[VOICE] Stop called but recorder is not in recording state:` warning
- Better error messages at each failure point

#### Important fix:
- Changed `recorder.start()` → `recorder.start(100)` to request audio chunks every 100ms
  This ensures chunks are collected regularly, not just on stop

### 2. API Client Logging (axios)
**File: `frontend/src/api.js`**

#### Added logging to all functions:
- `chatWithAgent()`: Logs message, language, response status
- `speakText()`: Logs text length, language, audio URL
- `transcribeAudio()`: Logs blob size, extension, language, response status

#### Improved error handling:
- Shows HTTP status code in errors: `[API] transcribeAudio error: {status: 502, message: "..."}`
- Shows full error response data for debugging
- Fixed transcribeAudio to properly send FormData multipart requests

### 3. Backend Logging (FastAPI/Python)
**File: `backend/app/routers/voice.py`**

#### Added detailed logging to `/api/voice/transcribe` endpoint:
- `Transcribe request: language=hi-IN, filename=audio.webm`
- `Processing audio: file=audio.webm, ext=webm, size=XXXX`
- `FFmpeg conversion: XXXX -> YYYY bytes` (shows audio size before/after)
- `Calling Sarvam STT API with YYYY bytes`
- `Sarvam STT response: status=200`
- `Sarvam Answer: 'transcript text' [Detected: language]`
- `Translating 'text' from detected_lang to en-IN`

#### Enhanced error messages:
- Better error details: `Sarvam STT Failed: {type(e).__name__}: {e}`
- Timeout detection: `Audio conversion failed: ...`
- FFmpeg missing warning: `ffmpeg not found — sending raw audio`
- Improved handling of silent audio detection

## How to Use These Changes

### For Users (Testing)
1. Go to https://tourmaline-centaur-75efe7.netlify.app/
2. Open browser Console (F12)
3. Try voice feature
4. Look for `[VOICE]` logs in console
5. Share the logs showing where it gets stuck

### For Debugging
1. **Check browser console** for `[VOICE]` and `[API]` logs
2. **Check Render backend logs** for transcription errors
3. **Compare logs** to identify exact failure point
4. **Apply specific fix** based on failure type

## Deployment Instructions

To deploy these changes to live site:

1. **Commit changes:**
   ```bash
   git add -A
   git commit -m "Add comprehensive voice pipeline logging for debugging"
   ```

2. **Push to main:**
   ```bash
   git push origin main
   ```

3. **Netlify will auto-deploy** (typically 2-3 minutes)

4. **Test on live site** at https://tourmaline-centaur-75efe7.netlify.app/

5. **Open console (F12)** and test voice feature

6. **Copy console logs** showing where it fails

## What the Logs Will Show

### ✅ Success Path
```
[VOICE] Starting recording...
→ [VOICE] Microphone stream acquired
→ [VOICE] Recording started
→ [VOICE] Stop signal sent
→ [VOICE] Recording stopped. Blob size: 45000
→ [VOICE] Calling transcribeAudio with language: hi-IN
→ [API] transcribeAudio: {blobSize: 45000, ext: "webm"}
→ [VOICE] Transcription response: {status: "SUCCESS", hasTranscript: true}
→ [VOICE] Transcription SUCCESS: "Namaste, kaise ho?"
→ [VOICE] Calling agent...
→ [VOICE] Agent response: {hasResponse: true}
→ [VOICE] Calling speak...
→ [VOICE] Audio URL generated, starting playback
✓ User hears AI response
```

### ❌ Failure Example 1: No Audio Capture
```
[VOICE] Recording stopped. Blob size: 0 bytes
⚠️ Error: "Audio capture failed. Please try again."
→ Check: Microphone permission, speaker audio presence
```

### ❌ Failure Example 2: API Timeout
```
[VOICE] Calling transcribeAudio with language: hi-IN
[API] transcribeAudio: {blobSize: 12345, ext: "webm"}
(nothing after 45+ seconds)
❌ Error: "Error processing voice. Try again."
→ Check: Backend logs, network connection, Sarvam API
```

### ❌ Failure Example 3: Sarvam Error
```
[VOICE] Calling transcribeAudio...
[API] transcribeAudio error: {status: 502, message: "Sarvam TTS error: 502"}
❌ Error: "Error processing voice. Try again."
→ Check: SARVAM_API_KEY in Render, API rate limits
```

## Next Steps

1. **Deploy** these changes to main branch
2. **Test** voice feature on live site
3. **Open console** and capture logs
4. **Identify** which log sequence you see
5. **Report** the exact failure point
6. Apply targeted fix based on failure

## Checklist Before Deployment

- [ ] All files edited correctly
- [ ] No syntax errors in frontend code
- [ ] Backend logging added properly
- [ ] Git changes staged
- [ ] Commit message written
- [ ] Ready to push to main

## Related Documentation

See `VOICE_DEBUGGING_GUIDE.md` for:
- Detailed failure point descriptions
- Manual testing procedures
- Backend log interpretation
- Quick fix checklist
