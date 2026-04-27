"""
KisaanVaani — Fix Verification Test
Tests: Gemini Vision + Full Agent Pipeline (3 real questions)
Run with backend ON port 8000.
"""
import asyncio, os, base64, time
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")
import httpx

GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
TEST_LAT, TEST_LON = 30.48, 76.59

def P(label, ok, detail="", t=None):
    icon = "[PASS]" if ok else "[FAIL]"
    ts   = f"  ({t}s)" if t else ""
    print(f"\n  {icon}  {label}{ts}")
    if detail:
        print(f"         {detail[:220]}")

# ── 1. GEMINI VISION ─────────────────────────────────────────────────────────
async def test_gemini():
    print("\n" + "="*62)
    print("  TEST 1 — Gemini Vision (gemini-2.0-flash)")
    print("="*62)

    if not GEMINI_KEY:
        P("Gemini Vision", False, "GEMINI_API_KEY missing in .env"); return False

    # 1x1 green PNG (smallest valid PNG)
    tiny_png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
        "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )

    t0 = time.time()
    try:
        # ── Path A: google-genai (new SDK) ────────────────────────────────
        try:
            from google import genai as gai
            from google.genai import types as gtypes
            print("  Using new google.genai SDK...")
            client = gai.Client(api_key=GEMINI_KEY)
            resp = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    "Describe this image in ONE sentence. It is a test image.",
                    gtypes.Part.from_bytes(data=tiny_png, mime_type="image/png"),
                ],
            )
            elapsed = round(time.time() - t0, 2)
            P("Gemini Vision [new SDK]", True,
              f"Response: {resp.text.strip()[:180]}", elapsed)
            return True

        except ImportError:
            print("  google.genai not installed — trying legacy SDK...")

        # ── Path B: google-generativeai (legacy) ──────────────────────────
        import google.generativeai as old_genai
        print("  Using legacy google.generativeai SDK...")
        old_genai.configure(api_key=GEMINI_KEY)
        model = old_genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(
            ["Describe this image in ONE sentence.", {"mime_type": "image/png", "data": tiny_png}]
        )
        elapsed = round(time.time() - t0, 2)
        P("Gemini Vision [legacy SDK]", True,
          f"Response: {resp.text.strip()[:180]}", elapsed)
        return True

    except Exception as e:
        elapsed = round(time.time() - t0, 2)
        P("Gemini Vision", False, f"Exception: {e}", elapsed)

        # Try to auto-detect if it's just the SDK path issue and fix it
        print("\n  [DEBUG] Checking available flash models...")
        try:
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(
                    f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
                )
                if r.status_code == 200:
                    flash = [
                        m["name"] for m in r.json().get("models", [])
                        if "flash" in m["name"] and "generateContent" in m.get("supportedGenerationMethods", [])
                    ]
                    print(f"  Available flash models: {flash[:5]}")
        except Exception as me:
            print(f"  Model list check failed: {me}")
        return False


# ── 2. FULL AGENT PIPELINE ───────────────────────────────────────────────────
async def test_agent_pipeline():
    print("\n" + "="*62)
    print("  TEST 2 — Full Agent Pipeline (3 real farming questions)")
    print("="*62)

    questions = [
        {
            "label": "Mandi Price — Hindi",
            "msg":   "Aaj Patiala mandi mein gehun ka kya bhav chal raha hai?",
            "eng":   "What is the current wheat price in Patiala mandi today?",
            "lang":  "hi-IN",
        },
        {
            "label": "Crop Disease — Punjabi",
            "msg":   "ਮੇਰੀ ਕਣਕ ਉੱਤੇ ਪੀਲੇ ਧੱਬੇ ਆ ਰਹੇ ਹਨ, ਕੀ ਕਰਾਂ?",
            "eng":   "Yellow spots are appearing on my wheat, what should I do?",
            "lang":  "pa-IN",
        },
        {
            "label": "Weather — English",
            "msg":   "What is the weather forecast for my farm near Rajpura today?",
            "eng":   "What is the weather forecast for my farm near Rajpura today?",
            "lang":  "en-IN",
        },
    ]

    all_pass = True
    async with httpx.AsyncClient(timeout=90, base_url="http://localhost:8000") as c:
        for i, q in enumerate(questions, 1):
            print(f"\n  --- Q{i}: {q['label']} ---")
            print(f"  User says ({q['lang']}): {q['msg'][:70]}")
            t0 = time.time()
            try:
                r = await c.post("/api/agent/chat", json={
                    "farmer_id":       "9999999999",
                    "session_id":      f"fix_test_{i}",
                    "message":         q["msg"],
                    "english_message": q["eng"],
                    "language":        q["lang"],
                    "image":           None,
                    "location": {"lat": TEST_LAT, "lon": TEST_LON, "city": "Rajpura"},
                })
                elapsed = round(time.time() - t0, 2)
                if r.status_code == 200:
                    data    = r.json()
                    reply   = data.get("response", "")
                    tool    = data.get("tool_used", "?")
                    P(f"Q{i} [{q['label']}]", True,
                      f"Tool: {tool} | Reply: {reply[:180]}...", elapsed)
                else:
                    P(f"Q{i} [{q['label']}]", False,
                      f"HTTP {r.status_code}: {r.text[:120]}", elapsed)
                    all_pass = False
            except Exception as e:
                elapsed = round(time.time() - t0, 2)
                P(f"Q{i} [{q['label']}]", False, f"Exception: {e}", elapsed)
                all_pass = False

    return all_pass


# ── MAIN ─────────────────────────────────────────────────────────────────────
async def main():
    print("\nKisaanVaani — Fix Verification (Gemini + Agent Pipeline)\n")
    g_ok  = await test_gemini()
    ag_ok = await test_agent_pipeline()

    print("\n" + "="*62)
    print("  SUMMARY")
    print("="*62)
    P("Gemini Vision (gemini-2.0-flash)", g_ok)
    P("Agent Pipeline (3 farming Qs)",   ag_ok)
    if g_ok and ag_ok:
        print("\n  ALL FIXED — App is ready!\n")
    else:
        print("\n  Some issues remain — see details above.\n")

asyncio.run(main())
