import asyncio, httpx

async def ask(msg, eng, lang, label):
    async with httpx.AsyncClient(timeout=60, base_url="http://localhost:8000") as c:
        r = await c.post("/api/agent/chat", json={
            "farmer_id": "9999999999", "session_id": "test_fix_final",
            "message": msg, "english_message": eng, "language": lang,
            "image": None, "location": {"lat": 30.48, "lon": 76.59, "city": "Rajpura"}
        })
        if r.status_code == 200:
            d = r.json()
            tool  = d.get("tool_used", "?")
            reply = d.get("response", "")[:250]
            print(f"\n[{label}]")
            print(f"  Tool used : {tool}")
            print(f"  Reply     : {reply}")
        else:
            print(f"\n[{label}] ERROR {r.status_code}: {r.text[:100]}")

async def main():
    print("\n=== Live Agent Routing Test ===\n")
    await ask(
        "Saharanpur kahan hai?", "Where is Saharanpur?", "hi-IN",
        "1. Geography Q — MUST use general_node, answer location"
    )
    await ask(
        "Kya haal hai aapka?", "How are you?", "hi-IN",
        "2. Greeting — MUST use general_node, warm reply"
    )
    await ask(
        "Gehun ka bhav kya hai aaj?", "What is wheat price today?", "hi-IN",
        "3. Mandi Q — MUST use mandi_node"
    )
    await ask(
        "Meri sarson pe peele dhabbe aa rahe hain", "Yellow spots on my mustard crop", "hi-IN",
        "4. Crop Disease — MUST use crop_advice_node"
    )

asyncio.run(main())
