import asyncio, httpx

NEW_KEY = "AIzaSyBoh4KYOKNsPEx9dVFX-3sLs6m3HHmBSx0"

async def check(key, label):
    async with httpx.AsyncClient(timeout=15) as c:
        r1 = await c.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}")
        print(f"\n{label}")
        print(f"  Models API: HTTP {r1.status_code}")
        if r1.status_code != 200:
            err = r1.json().get("error", {})
            print(f"  => INVALID KEY: {err.get('message','')[:120]}")
            return

        r2 = await c.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}",
            json={"contents": [{"parts": [{"text": "Reply with just the word OK"}]}]}
        )
        if r2.status_code == 200:
            parts = r2.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
            txt = parts[0].get("text", "") if parts else ""
            print(f"  Generate call: HTTP 200 — WORKING!")
            print(f"  Response: '{txt.strip()}'")
            print(f"  => KEY IS VALID AND HAS FREE QUOTA AVAILABLE")
        else:
            err  = r2.json().get("error", {})
            msg  = err.get("message", "")[:150]
            print(f"  Generate call: HTTP {r2.status_code}")
            print(f"  Message: {msg}")
            if "429" in str(r2.status_code) or "EXHAUSTED" in msg.upper() or "QUOTA" in msg.upper():
                print(f"  => KEY IS VALID BUT QUOTA EXHAUSTED (free limit hit — same problem as old key)")
            elif "403" in str(r2.status_code) or "INVALID" in msg.upper():
                print(f"  => KEY IS INVALID / NOT AUTHORIZED")

asyncio.run(check(NEW_KEY, "=== NEW KEY (AIzaSyBoh4...) ==="))
