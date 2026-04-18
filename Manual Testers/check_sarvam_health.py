import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv('backend/.env')
api_key = os.getenv('SARVAM_API_KEY')

async def check_sarvam():
    url = 'https://api.sarvam.ai/text-to-speech'
    headers = {
        'api-subscription-key': api_key,
        'Content-Type': 'application/json'
    }
    payload = {
        'inputs': ['Test'],
        'target_language_code': 'hi-IN',
        'speaker': 'ritu',
        'model': 'bulbul:v2'
    }
    
    print(f"Checking Sarvam AI with Key: {api_key[:5]}...{api_key[-5:]}")
    
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(url, json=payload, headers=headers)
            print(f"Status Code: {r.status_code}")
            if r.status_code == 200:
                print("SUCCESS: Credits are active and working!")
            elif r.status_code == 401 or r.status_code == 403:
                print("ERROR: Invalid API Key.")
            elif r.status_code == 429 or r.status_code == 402:
                print("ERROR: Credits exhausted (Limit reached).")
            else:
                print(f"ERROR: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"Network Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_sarvam())
