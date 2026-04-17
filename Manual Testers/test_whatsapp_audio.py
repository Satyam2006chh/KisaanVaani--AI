import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv("backend/.env")

SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

AUDIO_FILE = "WhatsApp Ptt 2026-04-17 at 10.43.47 PM.ogg"

async def test_audio_flow():
    if not os.path.exists(AUDIO_FILE):
        print(f"File not found: {AUDIO_FILE}")
        return

    print(f"--- 1. Testing Transcription for {AUDIO_FILE} ---")
    with open(AUDIO_FILE, "rb") as f:
        audio_bytes = f.read()

    # Sarvam STT (Handling OGG)
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            r = await client.post(
                "https://api.sarvam.ai/speech-to-text",
                headers={"api-subscription-key": SARVAM_API_KEY},
                files={"file": (AUDIO_FILE, audio_bytes, "audio/ogg")},
                data={
                    "model": "saarika:v2.5",
                    "language_code": "hi-IN"
                }
            )
            r.raise_for_status()
            res = r.json()
            transcript = res.get("transcript", "")
            print(f"Transcript: {transcript}")
        except Exception as e:
            print(f"Transcription failed: {e}")
            return

    if not transcript:
        print("Empty transcript, stopping.")
        return

    print("\n--- 2. Testing Agent Logic ---")
    # Simulate the Chat Endpoint
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            r = await client.post(
                "http://localhost:8000/api/agent/chat",
                json={
                    "farmer_id": "9876543210",
                    "session_id": "test_session",
                    "message": transcript,
                    "language": "hi-IN"
                }
            )
            r.raise_for_status()
            res = r.json()
            print(f"AI Response: {res['response']}")
            print(f"Tool Used: {res.get('tool_used')}")
        except Exception as e:
            print(f"Agent flow failed (Make sure backend is running): {e}")

if __name__ == "__main__":
    asyncio.run(test_audio_flow())
