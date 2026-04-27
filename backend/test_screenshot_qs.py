"""Test the exact questions from the screenshots"""
import asyncio, httpx

BASE = "http://localhost:8000"

PAYLOAD = {
    "farmer_id": "8445799110",
    "session_id": "screenshot_test_001",
    "language": "hi-IN",
    "image": None,
    "location": {"lat": 30.35, "lon": 76.37, "city": "Patiala", "district": "Patiala", "state": "Punjab"}
}

async def ask(hindi_msg, eng_msg, label):
    async with httpx.AsyncClient(timeout=90, base_url=BASE) as c:
        r = await c.post("/api/agent/chat", json={
            **PAYLOAD,
            "message": hindi_msg,
            "english_message": eng_msg
        })
    print(f"\n{'='*65}")
    print(f"QUESTION: {hindi_msg}")
    print(f"{'='*65}")
    if r.status_code == 200:
        d = r.json()
        print(f"TOOL USED : {d.get('tool_used')}")
        print(f"\nFULL AI RESPONSE:\n{d.get('response', '')}")
    else:
        print(f"ERROR {r.status_code}: {r.text[:300]}")

async def main():
    # Q1 from screenshot 1
    await ask(
        "फसल बीमा योजना के लिए लास्ट डेट कब है और कौन से डॉक्यूमेंट्स चाहिए",
        "What is the last date for Fasal Bima Yojana and what documents are required",
        "Screenshot Q1 - PMFBY"
    )
    await asyncio.sleep(1)
    # Q2 from screenshot 2
    await ask(
        "अपनी जमीन पर सोलर पंप लगवा सकता है सब्सिडी पे?",
        "Can I install solar pump on my land with subsidy?",
        "Screenshot Q2 - PM-KUSUM"
    )

asyncio.run(main())
