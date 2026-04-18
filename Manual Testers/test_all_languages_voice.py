import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv('backend/.env')
api_key = os.getenv('SARVAM_API_KEY')

async def test_all_languages():
    url = 'https://api.sarvam.ai/text-to-speech'
    headers = {
        'api-subscription-key': api_key,
        'Content-Type': 'application/json'
    }
    
    test_cases = [
        {"lang": "hi-IN", "text": "Namaste, main KisaanVaani AI hoon."},
        {"lang": "pa-IN", "text": "Sat Sri Akal, main KisaanVaani AI haan."},
        {"lang": "en-IN", "text": "Hello, I am KisaanVaani AI."},
        {"lang": "ta-IN", "text": "Vanakkam, naan KisaanVaani AI."},
        {"lang": "bn-IN", "text": "Namaskar, aami KisaanVaani AI."},
        {"lang": "gu-IN", "text": "Kem chho, hu KisaanVaani AI chhu."}
    ]
    
    print("\n" + "="*50)
    print(" TESTING SARVAM AI: BULBUL:V2 (MANISHA VOICE)")
    print("="*50 + "\n")
    
    async with httpx.AsyncClient(timeout=30) as client:
        for case in test_cases:
            payload = {
                'inputs': [case["text"]],
                'target_language_code': case["lang"],
                'speaker': 'manisha',
                'model': 'bulbul:v2'
            }
            
            try:
                r = await client.post(url, json=payload, headers=headers)
                status = "SUCCESS" if r.status_code == 200 else f"FAILED ({r.status_code})"
                print(f"[{case['lang']}] - {status}")
                if r.status_code != 200:
                    print(f"   Reason: {r.text[:100]}")
            except Exception as e:
                print(f"[{case['lang']}] - ERROR: {e}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    asyncio.run(test_all_languages())
