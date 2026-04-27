import asyncio, httpx

BASE = "http://localhost:8000"
PAYLOAD_BASE = {
    "farmer_id": "9999999999", "session_id": "mandi_test",
    "language": "hi-IN", "image": None,
    "location": {"lat": 30.9, "lon": 75.85, "city": "Ludhiana", "district": "Ludhiana", "state": "Punjab"}
}

async def ask(msg, eng, label):
    async with httpx.AsyncClient(timeout=60, base_url=BASE) as c:
        r = await c.post("/api/agent/chat", json={**PAYLOAD_BASE, "message": msg, "english_message": eng})
    if r.status_code == 200:
        d = r.json()
        print(f"\n[{label}]")
        print(f"  Tool : {d.get('tool_used')}")
        print(f"  Reply: {d.get('response','')[:300]}")
    else:
        print(f"\n[{label}] ERROR {r.status_code}: {r.text[:150]}")

async def main():
    print("\n=== MANDI ROUTING TESTS ===\n")
    # 1. Specific mandi name
    await ask(
        "Azadpur mandi mein gehun ka kya daam hai aaj?",
        "What is wheat price in Azadpur mandi today?",
        "Specific mandi name (Azadpur) — should extract Azadpur/Delhi"
    )
    # 2. User's own district
    await ask(
        "Mere zile ki mandi mein sarson ka kya bhav chal raha hai?",
        "What is mustard price in my district mandi?",
        "Mere zile ki mandi — should use profile district (Ludhiana, Punjab)"
    )
    # 3. Another city named
    await ask(
        "Karnal mandi mein dhan ka rate kya hai?",
        "What is paddy rate in Karnal mandi?",
        "Named city Karnal, Haryana"
    )

asyncio.run(main())
