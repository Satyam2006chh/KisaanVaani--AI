"""
Test: Does the agent remember previous answer when user says 'firse batao'?
This simulates a 2-turn conversation using the SAME session_id.
"""
import asyncio, httpx

BASE = "http://localhost:8000"
SESSION = "memory_test_001"
FARMER  = "9999999999"
LOCATION = {"lat": 29.96, "lon": 76.82, "city": "Karnal", "district": "Karnal", "state": "Haryana"}

async def ask(msg, eng, turn_label):
    async with httpx.AsyncClient(timeout=60, base_url=BASE) as c:
        r = await c.post("/api/agent/chat", json={
            "farmer_id": FARMER, "session_id": SESSION,
            "message": msg, "english_message": eng,
            "language": "hi-IN", "image": None, "location": LOCATION
        })
    if r.status_code == 200:
        d = r.json()
        print(f"\n{'='*60}")
        print(f"TURN: {turn_label}")
        print(f"USER: {msg}")
        print(f"TOOL: {d.get('tool_used')}")
        print(f"AI  : {d.get('response','')[:400]}")
    else:
        print(f"ERROR {r.status_code}: {r.text[:200]}")

async def main():
    print("\n🧠 MEMORY / CONTEXT TEST — Same session, 2 turns\n")

    # Turn 1: Real farming question
    await ask(
        "Haryana mein is season mein konsi fasal ugani chahiye?",
        "Which crop should I grow in Haryana this season?",
        "1 - Original farming question"
    )

    # Small wait to let save_message complete
    await asyncio.sleep(1)

    # Turn 2: Follow-up — AI should remember Turn 1's answer
    await ask(
        "firse batao mujhe samajh nahi aaya",
        "Please explain again, I didn't understand",
        "2 - Follow-up (SHOULD remember previous answer)"
    )

    await asyncio.sleep(1)

    # Turn 3: Even deeper follow-up
    await ask(
        "aur detail mein batao",
        "Tell me in more detail",
        "3 - Deeper follow-up"
    )

asyncio.run(main())
