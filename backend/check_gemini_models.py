"""Quick Gemini model list check"""
import os, asyncio
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")

async def find_models():
    import httpx
    print(f"Key: {GEMINI_KEY[:20]}...")
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
        )
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            models = r.json().get("models", [])
            flash_models = [m["name"] for m in models if "flash" in m["name"].lower() and "generate" in str(m.get("supportedGenerationMethods", []))]
            print("Flash models supporting generateContent:")
            for m in flash_models[:10]:
                print(f"  {m}")
        else:
            print(r.text[:300])

asyncio.run(find_models())
