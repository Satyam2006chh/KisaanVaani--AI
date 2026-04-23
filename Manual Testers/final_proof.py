import httpx
import asyncio
import sys
import os

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000").rstrip("/")

async def run():
    payload = {
        "farmer_id": "8445799110",
        "session_id": "final_proof",
        "message": "Main Rajpura (Punjab) mein hoon, mere sabse paas mandiyan batao.",
        "language": "hi-IN",
        "location": {"name": "Rajpura", "lat": 30.48, "lon": 76.59}
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{BASE_URL}/api/agent/chat", json=payload)
        sys.stdout.reconfigure(encoding='utf-8')
        print("\n=== AI RESPONSE FOR RAJPURA, PUNJAB ===")
        print(r.json()['response'])

if __name__ == "__main__":
    asyncio.run(run())
