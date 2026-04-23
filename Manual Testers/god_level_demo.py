import httpx
import asyncio
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://127.0.0.1:8000"

async def test_agent_interaction():
    # TEST DATA
    payload = {
        "farmer_id": "8445799110",
        "session_id": "final_god_level_test",
        "message": "Main Meerut mein hoon, yahan ka mausam kaisa hai aur Ganna (Sugarcane) ka MSP ya mandi bhav kya chal raha hai?",
        "language": "hi-IN",
        "location": {
            "name": "Meerut, Uttar Pradesh",
            "lat": 28.98,
            "lon": 77.71,
            "place": "Meerut",
            "state": "Uttar Pradesh"
        }
    }

    print("\n" + "="*80)
    print("🎤 QUESTION ASKED:")
    print(f"'{payload['message']}'")
    print(f"📍 Context: {payload['location']['name']}")
    print("="*80)

    async with httpx.AsyncClient(timeout=60) as client:
        try:
            print("⏳ AI AGENT IS THINKING...")
            r = await client.post(f"{BASE}/api/agent/chat", json=payload)
            
            if r.status_code == 200:
                response_data = r.json()
                answer = response_data.get("response", "")
                
                print("\n" + "🤖 AGENT RESPONSE (REASONING + TOOL DATA):")
                print("-" * 40)
                print(answer)
                print("-" * 40)
                print(f"🔍 Intent Used: {response_data.get('tool_used', 'N/A')}")
            else:
                print(f"❌ Error: {r.status_code}")
                print(r.text)
        except Exception as e:
            print(f"❌ Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_agent_interaction())
