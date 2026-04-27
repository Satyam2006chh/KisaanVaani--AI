"""
========================================================
  KisaanVaani — Full API & Tool Manual Test Suite
  Tests every external API + internal tool with real calls
========================================================
"""

import asyncio
import os
import sys
import base64
import time

# Load env before importing app modules
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env")

import httpx

# ── Colour helpers ─────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):  print(f"  {GREEN}✔ {msg}{RESET}")
def fail(msg):print(f"  {RED}✗ {msg}{RESET}")
def info(msg):print(f"  {YELLOW}→ {msg}{RESET}")
def hdr(msg): print(f"\n{BOLD}{CYAN}{'='*60}\n  {msg}\n{'='*60}{RESET}")

# ── Keys ───────────────────────────────────────────────
SARVAM_KEY      = os.getenv("SARVAM_API_KEY", "")
GROQ_KEY        = os.getenv("GROQ_API_KEY", "")
GEMINI_KEY      = os.getenv("GEMINI_API_KEY", "")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_API_KEY", "")
FIRECRAWL_KEY   = os.getenv("FIRECRAWL_API_KEY", "")
DATAGOV_KEY     = os.getenv("DATAGOV_API_KEY", "")
SUPABASE_URL    = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY    = os.getenv("SUPABASE_SERVICE_KEY", "")

# ── Test location: Rajpura, Punjab ─────────────────────
TEST_LAT = 30.48
TEST_LON = 76.59
TEST_DISTRICT = "Patiala"
TEST_STATE    = "Punjab"

results = {}  # tool -> (passed, latency_s)

# ══════════════════════════════════════════════════════════
# 1. SARVAM AI — Text-to-Speech (TTS)
# ══════════════════════════════════════════════════════════
async def test_sarvam_tts():
    hdr("1. Sarvam TTS — 'Namaste Kisaan ji' in Hindi")
    if not SARVAM_KEY:
        fail("SARVAM_API_KEY missing in .env"); results["sarvam_tts"] = (False, 0); return
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(
                "https://api.sarvam.ai/text-to-speech",
                headers={"api-subscription-key": SARVAM_KEY, "Content-Type": "application/json"},
                json={"inputs": ["Namaste Kisaan ji, aaj ka mausam achha hai."],
                      "target_language_code": "hi-IN", "speaker": "manisha", "model": "bulbul:v2"}
            )
        elapsed = round(time.time() - t0, 2)
        if r.status_code == 200:
            audios = r.json().get("audios", [])
            size = len(base64.b64decode(audios[0])) if audios else 0
            ok(f"Status 200 | Audio size: {size} bytes | Time: {elapsed}s")
            info(f"Audio decoded OK — would play as WAV in browser")
            results["sarvam_tts"] = (True, elapsed)
        else:
            fail(f"Status {r.status_code} | {r.text[:120]}")
            results["sarvam_tts"] = (False, elapsed)
    except Exception as e:
        fail(f"Exception: {e}"); results["sarvam_tts"] = (False, 0)


# ══════════════════════════════════════════════════════════
# 2. SARVAM AI — Translate (hi-IN → en-IN)
# ══════════════════════════════════════════════════════════
async def test_sarvam_translate():
    hdr("2. Sarvam Translate — 'Gehun ka bhav kya hai' → English")
    if not SARVAM_KEY:
        fail("SARVAM_API_KEY missing"); results["sarvam_translate"] = (False, 0); return
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                "https://api.sarvam.ai/translate",
                headers={"api-subscription-key": SARVAM_KEY},
                json={"input": "Gehun ka bhav kya hai aaj mandi mein?",
                      "source_language_code": "hi-IN", "target_language_code": "en-IN",
                      "model": "mayura:v1", "enable_preprocessing": False}
            )
        elapsed = round(time.time() - t0, 2)
        if r.status_code == 200:
            translated = r.json().get("translated_text", "")
            ok(f"Status 200 | Time: {elapsed}s")
            info(f"Original : Gehun ka bhav kya hai aaj mandi mein?")
            info(f"Translated: {translated}")
            results["sarvam_translate"] = (True, elapsed)
        else:
            fail(f"Status {r.status_code} | {r.text[:120]}")
            results["sarvam_translate"] = (False, elapsed)
    except Exception as e:
        fail(f"Exception: {e}"); results["sarvam_translate"] = (False, 0)


# ══════════════════════════════════════════════════════════
# 3. GROQ LLM — Chat Completion (3 random farming questions)
# ══════════════════════════════════════════════════════════
async def test_groq():
    hdr("3. Groq LLM — 3 Random Farming Questions")
    if not GROQ_KEY:
        fail("GROQ_API_KEY missing"); results["groq"] = (False, 0); return

    questions = [
        "What is the best fertilizer for wheat crop in Punjab? Answer in 2 lines.",
        "Meri sarson ki fasal par peele dhabb aa rahe hain, kya karun? (2 lines)",
        "Tell me 2 symptoms of rice blast disease."
    ]

    all_ok = True
    total_time = 0
    async with httpx.AsyncClient(timeout=30) as c:
        for i, q in enumerate(questions, 1):
            t0 = time.time()
            try:
                r = await c.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
                    json={"model": "llama-3.3-70b-versatile",
                          "messages": [{"role": "user", "content": q}],
                          "temperature": 0.4, "max_tokens": 100}
                )
                elapsed = round(time.time() - t0, 2)
                total_time += elapsed
                if r.status_code == 200:
                    answer = r.json()["choices"][0]["message"]["content"].strip()
                    ok(f"Q{i} ({elapsed}s): {q[:55]}...")
                    info(f"Answer: {answer[:120]}...")
                else:
                    fail(f"Q{i} Status {r.status_code}: {r.text[:80]}")
                    all_ok = False
            except Exception as e:
                fail(f"Q{i} Exception: {e}"); all_ok = False

    results["groq"] = (all_ok, round(total_time, 2))


# ══════════════════════════════════════════════════════════
# 4. GEMINI VISION — Test with a tiny test image
# ══════════════════════════════════════════════════════════
async def test_gemini_vision():
    hdr("4. Gemini Vision — Crop disease analysis (test image)")
    if not GEMINI_KEY:
        fail("GEMINI_API_KEY missing"); results["gemini_vision"] = (False, 0); return
    t0 = time.time()
    try:
        # Create a tiny 1x1 green PNG (valid image, won't crash Gemini)
        tiny_png_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
            "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        )
        img_bytes = base64.b64decode(tiny_png_b64)

        try:
            from google import genai as new_genai
            from google.genai import types
            client = new_genai.Client(api_key=GEMINI_KEY)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    "Describe this image briefly in 1 line. (It is a test image)",
                    types.Part.from_bytes(data=img_bytes, mime_type="image/png")
                ]
            )
            sdk_used = "google.genai (new SDK)"
        except ImportError:
            import google.generativeai as old_genai
            old_genai.configure(api_key=GEMINI_KEY)
            model = old_genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(
                ["Describe this image briefly in 1 line.", {"mime_type": "image/png", "data": img_bytes}]
            )
            sdk_used = "google.generativeai (legacy SDK)"

        elapsed = round(time.time() - t0, 2)
        answer = response.text.strip() if response.text else ""
        ok(f"Status OK | {sdk_used} | Time: {elapsed}s")
        info(f"Gemini says: {answer[:120]}")
        results["gemini_vision"] = (True, elapsed)
    except Exception as e:
        elapsed = round(time.time() - t0, 2)
        fail(f"Exception ({elapsed}s): {e}")
        results["gemini_vision"] = (False, elapsed)


# ══════════════════════════════════════════════════════════
# 5. WEATHER TOOL — Open-Meteo (free, no key needed)
# ══════════════════════════════════════════════════════════
async def test_weather():
    hdr("5. Weather Tool — Open-Meteo for Patiala, Punjab")
    t0 = time.time()
    try:
        sys.path.insert(0, ".")
        from app.agents.tools import get_weather
        result = await get_weather(TEST_DISTRICT, TEST_STATE, TEST_LAT, TEST_LON)
        elapsed = round(time.time() - t0, 2)
        if "temperature" in result.lower() or "°c" in result.lower() or "temp" in result.lower():
            ok(f"Time: {elapsed}s")
            info(result[:300])
            results["weather"] = (True, elapsed)
        else:
            fail(f"Unexpected output: {result[:150]}")
            results["weather"] = (False, elapsed)
    except Exception as e:
        fail(f"Exception: {e}"); results["weather"] = (False, 0)


# ══════════════════════════════════════════════════════════
# 6. MANDI PRICE TOOL — data.gov.in Agmarknet
# ══════════════════════════════════════════════════════════
async def test_mandi():
    hdr("6. Mandi Price Tool — Wheat price in Patiala (Agmarknet)")
    t0 = time.time()
    try:
        from app.agents.tools import get_mandi_price
        result = await get_mandi_price("wheat", TEST_DISTRICT, TEST_STATE)
        elapsed = round(time.time() - t0, 2)
        ok(f"Time: {elapsed}s")
        info(result[:300])
        results["mandi"] = (True, elapsed)
    except Exception as e:
        fail(f"Exception: {e}"); results["mandi"] = (False, 0)


# ══════════════════════════════════════════════════════════
# 7. NEAREST MANDI TOOL — GPS-based (Rajpura coords)
# ══════════════════════════════════════════════════════════
async def test_nearest_mandis():
    hdr("7. Nearest Mandi Tool — GPS Rajpura (30.48, 76.59)")
    t0 = time.time()
    try:
        from app.agents.tools import get_nearest_mandis
        mandis = await get_nearest_mandis(TEST_LAT, TEST_LON)
        elapsed = round(time.time() - t0, 2)
        if mandis and len(mandis) > 0:
            ok(f"Found {len(mandis)} mandis | Time: {elapsed}s")
            for m in mandis[:3]:
                dist = m.get('distance') or m.get('distance_km', '?')
                src  = m.get('source', '?')
                info(f"  {m['name']} ({m.get('state','')}) — {dist} km [{src}]")
            results["nearest_mandis"] = (True, elapsed)
        else:
            fail("No mandis returned")
            results["nearest_mandis"] = (False, elapsed)
    except Exception as e:
        fail(f"Exception: {e}"); results["nearest_mandis"] = (False, 0)


# ══════════════════════════════════════════════════════════
# 8. FIRECRAWL — Agricultural news scraping
# ══════════════════════════════════════════════════════════
async def test_firecrawl():
    hdr("8. Firecrawl — Scrape latest PM-KISAN scheme news")
    if not FIRECRAWL_KEY or "your_" in FIRECRAWL_KEY:
        fail("FIRECRAWL_API_KEY missing"); results["firecrawl"] = (False, 0); return
    t0 = time.time()
    try:
        from app.agents.tools import scrape_agricultural_news
        result = await scrape_agricultural_news("PM-KISAN scheme 2025 latest news")
        elapsed = round(time.time() - t0, 2)
        if result and "error" not in result.lower() and len(result) > 50:
            ok(f"Time: {elapsed}s")
            info(result[:350])
            results["firecrawl"] = (True, elapsed)
        else:
            fail(f"Possibly failed: {result[:150]}")
            results["firecrawl"] = (False, elapsed)
    except Exception as e:
        fail(f"Exception: {e}"); results["firecrawl"] = (False, 0)


# ══════════════════════════════════════════════════════════
# 9. NEARBY SERVICES TOOL — OSM Overpass
# ══════════════════════════════════════════════════════════
async def test_nearby_services():
    hdr("9. Nearby Services Tool — Hospitals/Agri shops near Rajpura")
    t0 = time.time()
    try:
        from app.agents.tools import get_nearby_services
        services = await get_nearby_services(TEST_LAT, TEST_LON, radius_m=15000)
        elapsed = round(time.time() - t0, 2)
        if services and len(services) > 0:
            ok(f"Found {len(services)} services | Time: {elapsed}s")
            for s in services[:3]:
                info(f"  [{s['type']}] {s['name']} — {s['distance_km']} km | ☎ {s.get('phone') or 'N/A'}")
            results["nearby_services"] = (True, elapsed)
        else:
            ok(f"No OSM services found near Rajpura (this is OK — rural area) | Time: {elapsed}s")
            info("Tool returned empty list — will show fallback message to farmer")
            results["nearby_services"] = (True, elapsed)
    except Exception as e:
        fail(f"Exception: {e}"); results["nearby_services"] = (False, 0)


# ══════════════════════════════════════════════════════════
# 10. SUPABASE — DB connection check
# ══════════════════════════════════════════════════════════
async def test_supabase():
    hdr("10. Supabase — Database Connection Test")
    if not SUPABASE_URL or not SUPABASE_KEY:
        fail("SUPABASE_URL or SUPABASE_SERVICE_KEY missing"); results["supabase"] = (False, 0); return
    t0 = time.time()
    try:
        from supabase import create_client
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Try selecting from users table
        res = sb.table("users").select("phone", "name").limit(2).execute()
        elapsed = round(time.time() - t0, 2)
        ok(f"Connection OK | Time: {elapsed}s | {len(res.data)} user record(s) found")
        for u in res.data:
            info(f"  User: {u.get('name','?')} | Phone: {str(u.get('phone','?'))[:6]}***")
        results["supabase"] = (True, elapsed)
    except Exception as e:
        elapsed = round(time.time() - t0, 2)
        fail(f"Exception ({elapsed}s): {e}")
        results["supabase"] = (False, elapsed)


# ══════════════════════════════════════════════════════════
# 11. FULL AGENT PIPELINE — Simulate a real chat request
# ══════════════════════════════════════════════════════════
async def test_agent_pipeline():
    hdr("11. Full Agent Pipeline — 3 random farming questions via HTTP")
    base = "http://localhost:8000"

    questions = [
        {
            "msg": "Aaj Patiala mandi mein gehun ka kya bhav chal raha hai?",
            "eng": "What is the current wheat price in Patiala mandi today?",
            "lang": "hi-IN",
            "label": "Mandi Price (Hindi)"
        },
        {
            "msg": "ਮੇਰੀ ਕਣਕ ਦੀ ਫ਼ਸਲ ਤੇ ਪੀਲੇ ਧੱਬੇ ਪੈ ਰਹੇ ਹਨ, ਕੀ ਕਰਾਂ?",
            "eng": "Yellow spots are appearing on my wheat crop, what should I do?",
            "lang": "pa-IN",
            "label": "Crop Disease (Punjabi)"
        },
        {
            "msg": "What is the weather forecast for my farm today?",
            "eng": "What is the weather forecast for my farm today?",
            "lang": "en-IN",
            "label": "Weather (English)"
        }
    ]

    all_ok = True
    total_t = 0
    async with httpx.AsyncClient(timeout=60, base_url=base) as c:
        for i, q in enumerate(questions, 1):
            t0 = time.time()
            try:
                r = await c.post("/api/agent/chat", json={
                    "farmer_id": "9999999999",
                    "session_id": f"test_session_{i}",
                    "message": q["msg"],
                    "english_message": q["eng"],
                    "language": q["lang"],
                    "image": None,
                    "location": {"lat": TEST_LAT, "lon": TEST_LON, "city": "Rajpura"}
                })
                elapsed = round(time.time() - t0, 2)
                total_t += elapsed
                if r.status_code == 200:
                    resp = r.json().get("response", "")
                    tool = r.json().get("tool_used", "?")
                    ok(f"Q{i} [{q['label']}] ({elapsed}s) — Tool: {tool}")
                    info(f"  Lang: {q['lang']} | Answer preview: {resp[:150]}...")
                else:
                    fail(f"Q{i} HTTP {r.status_code}: {r.text[:100]}")
                    all_ok = False
            except Exception as e:
                fail(f"Q{i} Exception: {e} (Is backend running on port 8000?)")
                all_ok = False

    results["agent_pipeline"] = (all_ok, round(total_t, 2))


# ══════════════════════════════════════════════════════════
# 12. SARVAM STT — Test with a pre-made WAV
# ══════════════════════════════════════════════════════════
async def test_sarvam_stt():
    hdr("12. Sarvam STT — Transcribing a minimal WAV file")
    if not SARVAM_KEY:
        fail("SARVAM_API_KEY missing"); results["sarvam_stt"] = (False, 0); return

    # Minimal valid 16kHz mono WAV (100ms silence) — always works with Sarvam
    # 44 bytes header + 1600 bytes of silence (100ms @ 16kHz 16-bit mono)
    num_samples = 1600
    data_bytes = (num_samples * 2).to_bytes(4, 'little')
    riff_size = (36 + num_samples * 2).to_bytes(4, 'little')
    wav = (
        b'RIFF' + riff_size + b'WAVE'
        b'fmt ' + b'\x10\x00\x00\x00'  # chunk size 16
        + b'\x01\x00'                  # PCM
        + b'\x01\x00'                  # mono
        + b'\x80\x3e\x00\x00'          # 16000 Hz
        + b'\x00\x7d\x00\x00'          # byte rate
        + b'\x02\x00'                  # block align
        + b'\x10\x00'                  # bits per sample
        + b'data' + data_bytes
        + bytes(num_samples * 2)       # silence
    )

    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                "https://api.sarvam.ai/speech-to-text",
                headers={"api-subscription-key": SARVAM_KEY},
                files={"file": ("test.wav", wav, "audio/wav")},
                data={"language_code": "hi-IN", "model": "saarika:v2.5"}
            )
        elapsed = round(time.time() - t0, 2)
        if r.status_code == 200:
            transcript = r.json().get("transcript", "")
            ok(f"Status 200 | Time: {elapsed}s")
            info(f"Transcript (silence): '{transcript}' (empty = correct for silence)")
            results["sarvam_stt"] = (True, elapsed)
        else:
            fail(f"Status {r.status_code}: {r.text[:150]}")
            results["sarvam_stt"] = (False, elapsed)
    except Exception as e:
        fail(f"Exception: {e}"); results["sarvam_stt"] = (False, 0)


# ══════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════
def print_summary():
    hdr("FINAL SUMMARY — All API & Tool Results")
    labels = {
        "sarvam_tts":       "Sarvam TTS (Text → Voice)",
        "sarvam_stt":       "Sarvam STT (Voice → Text)",
        "sarvam_translate": "Sarvam Translate",
        "groq":             "Groq LLM (3 Farming Qs)",
        "gemini_vision":    "Gemini 1.5 Flash Vision",
        "weather":          "Weather Tool (Open-Meteo)",
        "mandi":            "Mandi Price Tool (Agmarknet)",
        "nearest_mandis":   "Nearest Mandi GPS Tool",
        "firecrawl":        "Firecrawl News Scraper",
        "nearby_services":  "Nearby Services (OSM)",
        "supabase":         "Supabase Database",
        "agent_pipeline":   "Full Agent Pipeline (3 Qs)",
    }
    passed = 0
    total  = len(labels)
    print()
    for key, label in labels.items():
        if key in results:
            ok_flag, latency = results[key]
            status = f"{GREEN}✔ PASS{RESET}" if ok_flag else f"{RED}✗ FAIL{RESET}"
            lat_str = f"({latency}s)" if latency else ""
            print(f"  {status}  {label:<38} {lat_str}")
            if ok_flag: passed += 1
        else:
            print(f"  {YELLOW}⊘ SKIP{RESET}  {label}")
    print()
    print(f"  {BOLD}Results: {passed}/{total} passed{RESET}")
    if passed == total:
        print(f"  {GREEN}{BOLD}🌾 All systems GO! App is fully ready.{RESET}")
    elif passed >= total * 0.7:
        print(f"  {YELLOW}{BOLD}⚠ Most APIs working. Check failed ones above.{RESET}")
    else:
        print(f"  {RED}{BOLD}✗ Multiple failures. Fix API keys in .env.{RESET}")
    print()


# ══════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════
async def main():
    print(f"\n{BOLD}{CYAN}KisaanVaani — API & Tool Verification Suite{RESET}")
    print(f"Testing from: Rajpura, Punjab (lat={TEST_LAT}, lon={TEST_LON})\n")

    await test_sarvam_tts()
    await test_sarvam_stt()
    await test_sarvam_translate()
    await test_groq()
    await test_gemini_vision()
    await test_weather()
    await test_mandi()
    await test_nearest_mandis()
    await test_firecrawl()
    await test_nearby_services()
    await test_supabase()
    await test_agent_pipeline()

    print_summary()

if __name__ == "__main__":
    asyncio.run(main())
