import httpx
import asyncio
import json

BASE_URL = "http://127.0.0.1:8000" # Testing locally

TEST_LOCATIONS = [
    {"name": "Rajpura, Punjab", "lat": 30.48, "lon": 76.59},
    {"name": "Saharanpur, UP", "lat": 29.96, "lon": 77.55},
    {"name": "Karnal, Haryana", "lat": 29.68, "lon": 76.99}
]

async def test_agent(location_info):
    print(f"\n--- Testing for: {location_info['name']} ---")
    payload = {
        "farmer_id": "8445799110",
        "session_id": "test_session",
        "message": "Mere khet ke paas ki mandiyan aur vahan ka mausam batao.",
        "language": "hi-IN",
        "location": location_info
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(f"{BASE_URL}/api/agent/chat", json=payload)
            if r.status_code == 200:
                print(f"🤖 AI Answer: {r.json()['response']}")
            else:
                print(f"❌ Error: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"❌ Connection Error: {e}")

async def main():
    import sys
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass
        
    print("STARTING GOD LEVEL PROXIMITY TESTING...")
    for loc in TEST_LOCATIONS:
        await test_agent(loc)
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
