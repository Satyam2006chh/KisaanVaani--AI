import httpx
import asyncio

SARVAM_KEY = "sk_j2zqwag1_Xg6LcAfvy4elh22ki7Q36f3O"

async def test():
    # Test TTS
    print("Testing Sarvam TTS...")
    try:
        r = await httpx.AsyncClient(timeout=15).post(
            "https://api.sarvam.ai/text-to-speech",
            headers={"api-subscription-key": SARVAM_KEY, "Content-Type": "application/json"},
            json={"inputs": ["Namaste Kisaan ji"], "target_language_code": "hi-IN", "speaker": "manisha", "model": "bulbul:v2"}
        )
        print(f"TTS Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"TTS OK - got {len(data.get('audios', []))} audio(s)")
        else:
            print(f"TTS Error: {r.text[:200]}")
    except Exception as e:
        print(f"TTS Exception: {e}")

    # Test STT (translate a short text to check API key)
    print("\nTesting Sarvam Translate...")
    try:
        r2 = await httpx.AsyncClient(timeout=15).post(
            "https://api.sarvam.ai/translate",
            headers={"api-subscription-key": SARVAM_KEY},
            json={"input": "Hello farmer", "source_language_code": "en-IN", "target_language_code": "hi-IN", "model": "mayura:v1"}
        )
        print(f"Translate Status: {r2.status_code}")
        if r2.status_code == 200:
            print(f"Translate OK: {r2.json().get('translated_text')}")
        else:
            print(f"Translate Error: {r2.text[:200]}")
    except Exception as e:
        print(f"Translate Exception: {e}")

asyncio.run(test())
