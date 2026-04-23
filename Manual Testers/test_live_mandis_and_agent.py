"""
Comprehensive manual test:
1. Tests the live Agmarknet mandi API (via backend /mandis/nearby)
2. Tests the AI agent with 3 real locations: Chitkara (Punjab), Meerut (UP), Jaipur (Rajasthan)
3. Shows exactly what data the agent returns
"""
import httpx
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://127.0.0.1:8000"

TEST_LOCATIONS = [
    {"name": "Chitkara University (Punjab)", "lat": 30.51, "lon": 76.57},
    {"name": "Meerut (UP)",                  "lat": 28.98, "lon": 77.71},
    {"name": "Jaipur (Rajasthan)",           "lat": 26.91, "lon": 75.79},
]

async def test_mandis_nearby(loc):
    print(f"\n{'='*55}")
    print(f"📍 LOCATION: {loc['name']}")
    print(f"   Coords: {loc['lat']}, {loc['lon']}")
    print(f"{'='*55}")
    
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.post(f"{BASE}/api/agent/mandis/nearby", json={"lat": loc["lat"], "lon": loc["lon"]})
    
    if r.status_code != 200:
        print(f"❌ API Error: {r.status_code} - {r.text[:200]}")
        return
    
    mandis = r.json()
    if not mandis:
        print("⚠️  No mandis returned (empty list)")
        return
    
    print(f"✅ {len(mandis)} Mandis found — Source: {mandis[0].get('source', 'unknown').upper()}")
    for i, m in enumerate(mandis, 1):
        dist = f"{m['distance']} km" if m.get('distance') is not None else "N/A"
        price = m.get('price', 'No price data')
        print(f"  {i}. {m['name']} ({m.get('state','')}) | {dist} | {price}")

async def test_agent(loc):
    payload = {
        "farmer_id": "8445799110",
        "session_id": f"test_{loc['name'][:6]}",
        "message": "Mere aas paas ki mandiyan aur aaj ka mausam batao",
        "language": "hi-IN",
        "location": {"name": loc["name"], "lat": loc["lat"], "lon": loc["lon"]}
    }
    async with httpx.AsyncClient(timeout=40) as client:
        r = await client.post(f"{BASE}/api/agent/chat", json=payload)
    
    if r.status_code != 200:
        print(f"❌ Agent Error: {r.status_code}")
        return
    
    resp = r.json().get("response", "")
    print(f"\n🤖 AI AGENT RESPONSE ({loc['name']}):")
    print(f"{resp[:600]}...")

async def main():
    # Check server alive
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            h = await client.get(f"{BASE}/health")
        print("✅ Backend server is running!\n")
    except Exception:
        print("❌ Backend server is NOT running at port 8000!")
        print("   Please run: cd backend && uvicorn app.main:app --reload")
        return
    
    for loc in TEST_LOCATIONS:
        await test_mandis_nearby(loc)
        await test_agent(loc)
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
