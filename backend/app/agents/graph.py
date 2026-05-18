import asyncio
import logging
from typing import List, TypedDict

import httpx
from langgraph.graph import END, StateGraph

from app.agents.tools import get_mandi_price, get_weather, scrape_agricultural_news, get_nearby_services
from app.config import settings

logger = logging.getLogger(__name__)

# Unified Premium Speaker for Bulbul v2
SPEAKERS = {
    "hi-IN": "manisha", "pa-IN": "manisha", "bn-IN": "manisha",
    "ta-IN": "manisha", "te-IN": "manisha", "kn-IN": "manisha",
    "ml-IN": "manisha", "mr-IN": "manisha", "gu-IN": "manisha",
    "od-IN": "manisha", "as-IN": "manisha", "en-IN": "manisha",
}

LANG_MAP = {
    "hi-IN": "Hindi",  "pa-IN": "Punjabi", "bn-IN": "Bengali",
    "ta-IN": "Tamil",  "te-IN": "Telugu",  "en-IN": "English",
    "kn-IN": "Kannada","ml-IN": "Malayalam","mr-IN": "Marathi",
    "gu-IN": "Gujarati","od-IN": "Odia", "as-IN": "Assamese",
}


class AgentState(TypedDict):
    messages:         List[dict]
    farmer_id:        str
    farmer_name:      str
    language:         str
    city:             str
    district:         str
    state_name:       str
    intent:           str
    tool_result:      str
    final_answer:     str
    image_data:       str   # Base64
    original_message: str   # Raw user message in their language (for follow-up detection)


# ── Fallback Pipelines ────────────────────────────────────────────────────────
TEXT_MODELS = [
    "deepseek/deepseek-r1",                # 1. Reasoning Model (extremely powerful & cheap)
    "google/gemini-2.5-flash",             # 2. Fast and stable conversational model
    "google/gemini-2.5-flash:free",        # 3. 100% Free Gemini text model
    "anthropic/claude-3.5-sonnet",         # 4. Premium precision
    "meta-llama/llama-3.3-70b-instruct:free" # 5. 100% Free high-end conversational model
]

VISION_MODELS = [
    "google/gemini-2.5-flash",             # Extremely fast, highly accurate, and very cost-effective
    "google/gemini-2.5-flash:free",        # 100% Free Gemini fallback vision
    "anthropic/claude-3.5-sonnet",         # Premium high precision
    "openai/gpt-4o",                       # Premium high stability
    "meta-llama/llama-3.2-11b-vision-instruct:free" # 100% Free Llama fallback vision
]


async def _call_openrouter_text(messages: list, max_tokens: int = 900) -> str:
    """Sends text queries to OpenRouter, cascading through the 3 most powerful models in the world."""
    if not settings.openrouter_api_key or "your_" in settings.openrouter_api_key:
        print("WARNING: OpenRouter key not configured in .env.")
        return "[MOCK RESPONSE] Namaste! Main aapka KisaanVaani AI assistant hoon. Kripya admin se `.env` mein `OPENROUTER_API_KEY` set karne ke liye boleing."

    last_err = None
    for model in TEXT_MODELS:
        try:
            logger.info(f"Attempting OpenRouter text query with: {model}")
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.openrouter_api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://kisaanvaani.in",
                        "X-Title": "KisaanVaani"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": 0.4,
                        "max_tokens": max_tokens
                    },
                )
            if r.status_code == 200:
                logger.info(f"OpenRouter text model {model} succeeded")
                return r.json()["choices"][0]["message"]["content"]
            else:
                err_text = r.text[:200]
                logger.error(f"OpenRouter model {model} failed ({r.status_code}): {err_text}")
                last_err = f"HTTP {r.status_code}: {err_text}"
        except Exception as e:
            logger.error(f"OpenRouter model {model} exception: {e}")
            last_err = str(e)
            continue

    logger.error(f"All 3 powerful OpenRouter text models failed! Last error: {last_err}")
    return "Maaf kijiye, humare sabhi premium AI models abhi vyast (busy) hain. Kripya 2 minute baad dobara koshish karein."


async def _call_openrouter_vision(prompt: str, image_base64: str) -> str:
    """Diagnoses crop disease from pictures cascading across the 3 most powerful vision models in the world."""
    if not settings.openrouter_api_key or "your_" in settings.openrouter_api_key:
        return "Adarniya ji, fasal ki photo analyze karne ke liye `OPENROUTER_API_KEY` set hona zaroori hai. Kripya admin se sampark karein."

    import base64 as b64
    logger.info("Attempting OpenRouter Multimodal Vision cascade")

    mime_type = "image/jpeg"
    raw_b64   = image_base64
    if raw_b64.startswith("data:"):
        header, raw_b64 = raw_b64.split(",", 1)
        if "png"  in header: mime_type = "image/png"
        elif "webp" in header: mime_type = "image/webp"

    last_err = None
    for model in VISION_MODELS:
        try:
            logger.info(f"Attempting OpenRouter Vision Model: {model}")
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.openrouter_api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://kisaanvaani.in",
                        "X-Title": "KisaanVaani"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{mime_type};base64,{raw_b64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "temperature": 0.3,
                        "max_tokens": 800
                    }
                )
            if r.status_code == 200:
                logger.info(f"OpenRouter Vision model {model} succeeded")
                return r.json()["choices"][0]["message"]["content"]
            else:
                err_text = r.text[:200]
                logger.error(f"OpenRouter Vision model {model} failed: {r.status_code} - {err_text}")
                last_err = f"HTTP {r.status_code}: {err_text}"
        except Exception as e:
            logger.error(f"OpenRouter Vision model {model} exception: {e}")
            last_err = str(e)
            continue

    logger.error(f"All 3 powerful OpenRouter vision models failed! Last error: {last_err}")
    return await _openrouter_vision_fallback(prompt)



async def _openrouter_vision_fallback(original_prompt: str) -> str:
    """When vision fails, use OpenRouter text to give a text-based crop advisory."""
    logger.info("Using OpenRouter text-only fallback for vision query")
    fallback_prompt = (
        "The farmer uploaded a photo of a diseased crop, but image-analysis is temporarily "
        "unavailable. Based on the farmer query below, provide a VERY helpful "
        "general crop disease advisory in the farmer's language. "
        "List the 3 most common diseases for typical Indian crops, their visible symptoms, and treatment. "
        "Be specific and actionable.\n\n"
        f"Farmer context:\n{original_prompt[:600]}"
    )
    try:
        result = await _call_openrouter_text(
            [{"role": "system", "content": fallback_prompt}],
            max_tokens=450,
        )
        return "[Photo AI temporarily unavailable — general disease advice]\n\n" + result
    except Exception as e:
        logger.error(f"OpenRouter vision fallback also failed: {e}")
        return (
            "Adarniya ji, abhi tasveer analyze karne ki suvidha temporarily band hai. "
            "Kripya thodi der baad dobara koshish karein, ya bina tasveer ke apni fasal ki "
            "bimari ka description bolkar poochein — main zaroor madad karunga!"
        )


def _clean_location(val: str) -> str:
    """Return cleaned location or empty string if it's a test/dummy value."""
    if not val:
        return ""
    lower = val.lower().strip()
    # Hide test/dummy/empty profile values from AI
    junk = {"test", "test district", "test state", "n/a", "na", "none", "null", "undefined", "unknown"}
    if lower in junk or lower.startswith("test "):
        return ""
    return val.strip()


def _system_prompt(state: AgentState) -> str:
    lang_name = LANG_MAP.get(state["language"], "Hindi")

    district = _clean_location(state.get("district", ""))
    st       = _clean_location(state.get("state_name", ""))
    loc_str  = f"{district}, {st}" if district and st else (district or st or "India")

    # Sanitize name — strip test/empty/invalid values, NEVER let old history names through
    name = (state.get("farmer_name") or "").strip()
    if not name or name.lower() in {"kisaan", "test", "none", "null", "user", ""}:
        name = "Kisaan"

    return (
        "You are KisaanVaani AI — India's most trusted voice assistant for farmers.\n"
        f"Language: {lang_name} only.\n\n"
        "═══════════════════════════════════════════\n"
        f"⚠️  FARMER NAME (PERMANENT): {name}\n"
        f"⚠️  FARMER LOCATION: {loc_str}\n"
        "═══════════════════════════════════════════\n"
        f"CRITICAL — NAME RULE: You MUST address this farmer as '{name} ji' in EVERY response.\n"
        "If any previous message in history used a DIFFERENT name — IGNORE IT COMPLETELY.\n"
        "The name above is the ONLY correct, authoritative name. Never use any other name.\n\n"
        "⚠️  LANGUAGE RULE (MOST IMPORTANT):\n"
        f"  - ALL your responses MUST be in {lang_name} ONLY.\n"
        "  - User messages may appear in English because they are AUTO-TRANSLATED for processing.\n"
        "  - This does NOT mean the user wants English replies.\n"
        "  - NEVER say 'I cannot answer in English' or apologize about language.\n"
        f"  - Just answer directly in {lang_name}. Always.\n\n"
        "ABSOLUTE RULES (never break):\n"
        "1. ANSWER WHAT WAS ASKED — answer the exact question directly. Don't add generic advice unless explicitly asked.\n"
        "2. NO MARKDOWN: Never use symbols like *, **, #, or _ in your final response. Keep text plain and natural.\n"
        "3. Complete your answer fully — never stop mid-sentence.\n"
        "4. No hallucination — if data unavailable, say so clearly.\n"
        "5. No filler: Avoid generic sentences like 'I hope this is helpful' or 'Please contact me for more'. Be professional.\n"
        "6. Safety — no harmful or dangerous advice.\n"
    ).replace("{name}", name)



async def intent_router(state: AgentState) -> AgentState:
    msg = state["messages"][-1]["content"].lower().strip()

    # 0. VISION PRIORITY: image present → always vision
    img = state.get("image_data")
    if img and len(str(img)) > 100:
        return {**state, "intent": "vision"}

    # 1. FOLLOW-UP DETECTION — check BOTH English (msg) AND original language
    # This handles: "firse batao" (Hindi), "explain again" (English), etc.
    original = state.get("original_message", "").lower().strip()
    check_in  = msg + " " + original  # combined — match in either language

    FOLLOWUP_PHRASES = [
        # Hindi follow-up phrases
        "firse batao", "fir se batao", "samajh nahi aaya", "samajh nahi aya",
        "dobara batao", "phir batao", "repeat karo", "wahi batao",
        "aur detail", "thoda aur", "aur samjhao", "aur samjhaao",
        "pehle wala", "jo bataya tha", "iska matlab", "matlab kya",
        "clear nahi", "aur bata", "aur batao",
        # English follow-up phrases
        "explain again", "again please", "repeat that", "say again",
        "didn't understand", "not understand", "not clear", "more detail",
        "tell me more", "elaborate", "i don't understand", "can you explain",
        "what do you mean", "what does that mean", "please repeat",
    ]
    if any(phrase in check_in for phrase in FOLLOWUP_PHRASES):
        prev_intents = []
        for m in state["messages"][:-1]:
            content_lower = m.get("content", "").lower()
            if m.get("role") == "user":
                if any(w in content_lower for w in ["mausam", "baarish", "rain", "weather", "tapman", "forecast"]):
                    prev_intents.append("weather")
                elif any(w in content_lower for w in ["bhav", "mandi", "rate", "keemat", "price", "daam", "market"]):
                    prev_intents.append("mandi")
                elif any(w in content_lower for w in ["fasal", "crop", "ugao", "kheti", "beej", "khad",
                                                       "fertilizer", "keet", "grow", "cultivate", "harvest",
                                                       "soil", "mitti", "disease", "bimari"]):
                    prev_intents.append("crop_advice")
                elif any(w in content_lower for w in ["news", "yojana", "scheme", "subsidy", "samachar", "government"]):
                    prev_intents.append("news")
        if prev_intents:
            inherited = prev_intents[-1]
            logger.info(f"Follow-up detected — inheriting: {inherited}")
            return {**state, "intent": inherited}


    # 2. Fast keyword match for specific tool intents
    keywords = {
        "weather":        ["mausam", "mousam", "mosam", "baarish", "rain", "weather", "barsat", "temperature", "tapman"],
        "mandi":          ["bhav", "mandi", "rate", "keemat", "price", "daam", "bikri", "sell"],
        "vision":         ["bimari kya hai", "photo", "image", "pesticide", "fungus"],
        "crop_advice":    ["fasal", "crop", "ugao", "kheti", "kya lagao", "beej", "seed", "fertilizer", "khad", "keet"],
        "news":           ["news", "samachar", "khabar", "taza", "yojana", "scheme", "labh", "benefit", "subsidy", "latest"],
        "eligibility":    ["eligible", "patrata", "apply", "registration"],
        "trusted_vendor": ["vendor", "dealer", "shop", "doctor", "hospital", "clinic", "soil lab", "agri officer", "nearby"],
        "lang_switch":    ["punjabi mein", "hindi mein", "english mein", "tamil mein", "gujarati mein",
                           "bengali mein", "marathi mein", "bhasha badlo", "language change", "mein bolo", "mein jawab do"],
        # General: geography, greetings — NOTE: removed 'batao'/'bata do' (too broad, causes false positives)
        "general":        ["kahan hai", "kahan par hai", "kahaan h", "where is", "where are", "location of",
                           "kitni door", "distance", "kaun sa state", "which state", "capital of",
                           "kya hota hai", "what is", "what are",
                           "namaste", "hello", "hi ", "shukriya", "dhanyawad", "thanks",
                           "aap kaun", "who are you", "kisaanvaani kya"],
    }

    for intent, words in keywords.items():
        if any(w in msg for w in words):
            return {**state, "intent": intent}

    # 3. LLM fallback
    intent_prompt = (
        "You are an intent classifier for KisaanVaani, an AI assistant for Indian farmers.\n"
        "Classify the user message into EXACTLY ONE of these labels:\n"
        "  weather        — asking about rain, temperature, forecast\n"
        "  mandi          — asking about crop prices, market rates\n"
        "  crop_advice    — asking about crop care, fertilizers, seeds, pests\n"
        "  news           — asking about government schemes, subsidies, agri news\n"
        "  trusted_vendor — asking about nearby shops, doctors, agri offices\n"
        "  general        — geography, greetings, off-topic, general knowledge\n\n"
        "Return ONLY the label. No punctuation, no explanation.\n"
        f"Message: {msg}"
    )
    try:
        raw    = await _call_openrouter_text([{"role": "system", "content": intent_prompt}], max_tokens=10)
        intent = raw.strip().lower().replace(".", "").replace("`", "").split()[0]
        valid  = {"weather", "mandi", "crop_advice", "news", "trusted_vendor", "general"}
        if intent not in valid:
            intent = "general"
    except Exception:
        intent = "general"

    return {**state, "intent": intent}



async def weather_node(state: AgentState) -> AgentState:
    district = state["district"]
    state_name = state["state_name"]

    # Check if user asked about a DIFFERENT city
    messages = [
        {"role": "system", "content": (
            "Identify whether user asked weather for a specific city different from current location. "
            "Return strict JSON only: {\"city\": \"<name>\"} OR {\"city\": null}. "
        )},
        {"role": "user", "content": state["messages"][-1]["content"]},
    ]
    try:
        raw = await _call_openrouter_text(messages, max_tokens=30)
        import json
        params = json.loads(raw.strip())
        asked_city = params.get("city")
        if asked_city and asked_city not in ("null", "None", None, ""):
            weather_data = await get_weather(asked_city, state_name)
            location_label = asked_city
        else:
            weather_data = await get_weather(district, state_name)
            location_label = district
    except Exception:
        weather_data = await get_weather(district, state_name)
        location_label = district

    messages = [
        {"role": "system", "content": (
            f"{_system_prompt(state)}\n\n"
            f"Location: {location_label}\n"
            f"Weather Data: {weather_data}\n"
            "Include: current condition, rain probability, risk level, and 2 concrete farm actions."
        )},
    ]
    for m in state["messages"]:
        messages.append({"role": m["role"], "content": m["content"]})
    result = await _call_openrouter_text(messages)
    return {**state, "tool_result": result}



async def mandi_node(state: AgentState) -> AgentState:
    import json

    user_msg   = state["messages"][-1]["content"]
    profile_district = _clean_location(state.get("district", "")) or "Delhi"
    profile_state    = _clean_location(state.get("state_name", "")) or "Delhi"

    # Step 1: Use LLM to extract crop + target district from the user's message
    extract_prompt = (
        "You are a mandi price analyst for Indian agriculture.\n"
        f"Farmer profile: district='{profile_district}', state='{profile_state}'.\n\n"
        "From the user message below, extract:\n"
        "  - commodity : the crop/commodity in English (e.g. wheat, rice, sarson, soybean)\n"
        "  - district  : the mandi/district the user is asking about.\n"
        "    * If user says 'mere zile' / 'apne ilake' / 'my district' / no specific place → use the profile district above.\n"
        "    * If user names a specific mandi or city (e.g. 'Azadpur', 'Ludhiana', 'Karnal') → use that.\n"
        "  - state     : the state the district belongs to. Use profile state if unknown.\n\n"
        "Return ONLY valid JSON like: {\"commodity\": \"wheat\", \"district\": \"Patiala\", \"state\": \"Punjab\"}\n"
        "No explanation. No markdown.\n\n"
        f"User message: {user_msg}"
    )

    dist = profile_district
    st   = profile_state
    crop = "wheat"
    try:
        raw  = await _call_openrouter_text([{"role": "system", "content": extract_prompt}], max_tokens=60)
        # Strip any markdown code fences if present
        clean = raw.strip().strip("```json").strip("```").strip()
        params = json.loads(clean)
        crop = params.get("commodity", crop).lower().strip()
        dist = params.get("district", dist) or dist
        st   = params.get("state",     st)   or st
    except Exception as parse_err:
        logger.warning(f"Mandi param extraction failed: {parse_err} | raw='{raw[:80]}'")

    # Step 2: Fetch mandi price data
    mandi_data = await get_mandi_price(crop, dist, st)

    # Step 3: Compose final answer
    advice_msg = [
        {"role": "system", "content": (
            f"{_system_prompt(state)}\n\n"
            f"MANDI DATA — {crop.title()} in {dist}, {st}:\n{mandi_data}\n\n"
            "TASK: Give a clear, practical mandi price report to the farmer.\n"
            "Include: (a) current price / MSP reference, (b) whether it's a good time to sell, "
            "(c) one negotiation tip. If data is unavailable, say so clearly and suggest "
            f"checking nearby mandis or calling the local APMC in {dist}."
        )},
        {"role": "user", "content": user_msg},
    ]
    try:
        result = await _call_openrouter_text(advice_msg)
    except Exception:
        result = f"Maaf kijiye, {dist} ki mandi mein {crop} ka data abhi nahi mil raha. Kripya thodi der baad dobara poochein."

    return {**state, "tool_result": result}



async def news_node(state: AgentState) -> AgentState:
    lang_name   = LANG_MAP.get(state["language"], "Hindi")
    # Use original language message for scraping (more accurate keywords)
    user_question = state.get("original_message") or state["messages"][-1]["content"]

    # Built-in scheme knowledge base (fallback when scraping fails/is vague)
    SCHEME_KB = """
    PM-KISAN: Rs 6000/year in 3 installments. Eligibility: small/marginal farmers with land < 2 hectares.
      Documents: Aadhaar, land records (khasra/khatauni), bank passbook. Register at pmkisan.gov.in or CSC.
    PMFBY (Fasal Bima Yojana): Crop insurance. Premium: 2% for Kharif, 1.5% for Rabi, 5% for commercial.
      Last date: Usually 10-15 days before sowing cutoff date (varies by state and crop).
      Documents: Aadhaar, land records, bank account, sowing certificate from patwari.
      Check state agriculture dept website or call 1800-180-1551.
    PM-KUSUM (Solar Pump): 60-90% subsidy on solar pumps (30% central + 30% state + farmer pays 10-40%).
      Eligibility: Any farmer with agricultural land and own water source.
      Documents: Aadhaar, land records, bank account, water source proof.
      Apply: State DISCOM office or state agriculture portal.
    Kisan Credit Card (KCC): Short-term crop loan at 4% interest (2% subvention + 3% prompt repayment incentive).
      Limit: Based on crop + land. Apply at any nationalized bank or cooperative bank.
    e-NAM (Mandi Portal): Online mandi platform. Register at enam.gov.in for better price discovery.
    """

    # 1. Scrape live content
    raw_content = await scrape_agricultural_news(user_question)

    # 2. Compose answer using BOTH scraped data AND built-in KB
    messages = [
        {"role": "system", "content": (
            f"{_system_prompt(state)}\n\n"
            "You are an expert on Indian agricultural government schemes and policies.\n"
            f"FARMER'S QUESTION: {user_question}\n\n"
            "Use the information below to give a COMPLETE, SPECIFIC answer:\n"
            f"--- LIVE SCRAPED DATA ---\n{raw_content[:1500]}\n\n"
            f"--- SCHEME KNOWLEDGE BASE ---\n{SCHEME_KB}\n\n"
            "TASK: Give a COMPLETE answer that includes:\n"
            "  1. Specific scheme name(s) relevant to the question\n"
            "  2. Exact eligibility criteria\n"
            "  3. Required documents (list them specifically)\n"
            "  4. How to apply / where to go\n"
            "  5. Deadline/important dates if asked\n"
            f"Answer in {lang_name}. Be specific. Never give vague generic answers."
        )},
        {"role": "user", "content": user_question},
    ]
    formatted_result = await _call_openrouter_text(messages, max_tokens=1000)
    return {**state, "tool_result": formatted_result}


async def llm_node(state: AgentState) -> AgentState:
    user_msg = state["messages"][-1]["content"]
    lang_name = LANG_MAP.get(state["language"], "Hindi")
    
    if state["image_data"]:
        # Vision Path - ULTRA EXPERT SCIENTIST MODE
        
        # Smart detection: Did the farmer explicitly ask to EXCLUDE solutions/treatments?
        msg_lower = (user_msg + " " + state.get("original_message", "")).lower()
        exclude_solutions = any(
            w in msg_lower 
            for w in [
                "solution na", "solution mat", "solution nahi", "solution nahi chahiye",
                "ilaaj mat", "ilaaj na", "ilaaj nahi", "treatment mat", "treatment na", 
                "only problem", "problem kya hai", "only disease", "no treatment", "no solution",
                "sirf bimari", "sirf problem"
            ]
        )
        
        if exclude_solutions:
            prompt = (
                f"SYSTEM ROLE: You are a world-renowned Senior Agri-Scientist and Expert Plant Pathologist. "
                f"The farmer ({state['farmer_name']}) has sent a photo and asked: '{user_msg}'.\n"
                f"CRITICAL REQUIREMENT: The farmer has explicitly requested to ONLY identify the disease/problem and NOT include any treatment, solutions, chemical or organic cures, or prevention steps. Respect this completely.\n\n"
                "TASK: Analyze this image and generate a professional, high-precision 'SCIENTIFIC CROP HEALTH REPORT'.\n"
                "IMPORTANT: Your identification must be 100% accurate. Do not be generic. Use scientific names.\n\n"
                f"REPORT CONTENT (Strictly follow this structure in {lang_name}):\n"
                "1. IDENTIFICATION: Common Name & *Scientific Name* (Italicized).\n"
                "2. THE CAUSE (WHY IT HAPPENED): Explain the root cause. Did it come from soil? High humidity? Poor ventilation? Nutrient deficiency?\n"
                "3. THE SPREAD (LIFECYCLE): How does this disease spread?\n"
                "4. KEY SYMPTOMS: List 3 specific indicators visible in the photo that confirm your diagnosis.\n\n"
                f"Tone: Authoritative, Professional, and Caring. Final output language must be only {lang_name}."
            )
        else:
            prompt = (
                f"SYSTEM ROLE: You are a world-renowned Senior Agri-Scientist and Expert Plant Pathologist. "
                f"The farmer ({state['farmer_name']}) has sent a photo and asked: '{user_msg}'.\n\n"
                "TASK: Analyze this image and generate a professional, high-precision 'SCIENTIFIC CROP HEALTH REPORT'.\n"
                "IMPORTANT: Your identification must be 100% accurate. Do not be generic. Use scientific names.\n\n"
                f"REPORT CONTENT (Strictly follow this structure in {lang_name}):\n"
                "1. IDENTIFICATION: Common Name & *Scientific Name* (Italicized).\n"
                "2. THE CAUSE (WHY IT HAPPENED): Explain the root cause. Did it come from soil? High humidity? Poor ventilation? Nutrient deficiency? Explain scientifically but clearly.\n"
                "3. THE SPREAD (LIFECYCLE): How does this disease spread? (e.g., wind-borne spores, water-splash, or pests like Thrips/Aphids).\n"
                "4. KEY SYMPTOMS: List 3 specific indicators visible in the photo that confirm your diagnosis.\n"
                "5. TREATMENT (IMMEDIATE): Recommend 2 effective chemical treatments with exact dosages (e.g., grams per liter).\n"
                "6. ORGANIC CURE: Provide 1-2 reliable organic or home-made solutions (e.g., Neem, Trichoderma).\n"
                "7. LONG-TERM PREVENTION: 3 practical steps to ensure this never happens again (e.g., Crop rotation, Soil solarization).\n\n"
                f"Tone: Authoritative, Professional, and Caring. Final output language must be only {lang_name}."
            )
        # Call vision with specific prompt
        result = await _call_openrouter_vision(prompt, state["image_data"])
    else:
        # Standard Path - CONTEXT AWARE MODE
        # Check if history contains a previous diagnosis to maintain context
        history_context = ""
        if len(state["messages"]) > 1:
            history_context = "\nCONTEXT: Use the previous conversation history to answer follow-up questions about crops or diseases mentioned earlier."

        messages = [
            {"role": "system", "content": (
                f"{_system_prompt(state)}\n\n"
                f"Aap ek expert scientist hain. {history_context}\n"
                "Provide a detailed, robust, and professional answer. "
                "If the user is asking about the diagnosis you just gave, explain further in detail. "
                "Tone: Senior Scientist, Expert, and Encouraging."
            )},
        ]
        # Prepend history and current message
        for m in state["messages"]:
             messages.append({"role": m["role"], "content": m["content"]})
             
        result = await _call_openrouter_text(messages)
        
    return {**state, "tool_result": result}


async def lang_switch_node(state: AgentState) -> AgentState:
    msg = state["messages"][-1]["content"].lower()
    
    # 1. Quick find
    new_lang = state["language"]
    for code, name in LANG_MAP.items():
        if name.lower() in msg:
            new_lang = code
            break
            
    # 2. LLM validation if needed
    if new_lang == state["language"]:
        prompt = (
            "User wants to change response language. Identify the target language code from this list: "
            f"{list(LANG_MAP.keys())}. If mentioned language is Punjabi, use 'pa-IN'. "
            "Return ONLY the code. If not clear, return current: " + state["language"] + "\n\n"
            "Query: " + msg
        )
        try:
            detected = await _call_openrouter_text([{"role": "system", "content": prompt}], max_tokens=10)
            detected = detected.strip()
            if detected in LANG_MAP:
                new_lang = detected
        except Exception:
            pass

    lang_name = LANG_MAP.get(new_lang, "Hindi")
    return {
        **state, 
        "language": new_lang, 
        "tool_result": f"Theek hai, ab se main aapko {lang_name} mein jawab doonga. Main aapki kaise madad kar sakta hoon?"
    }


async def crop_advice_node(state: AgentState) -> AgentState:
    lang_name = LANG_MAP.get(state["language"], "Hindi")

    has_history = len(state["messages"]) > 1
    context_note = (
        "\nIMPORTANT: The conversation history below contains earlier questions and answers. "
        "If the user is asking for clarification, repetition, or a follow-up, use that history to give a contextual answer."
        if has_history else ""
    )

    messages = [
        {"role": "system", "content": (
            f"{_system_prompt(state)}\n\n"
            "You are an expert Agri-Scientist. Give deep, practical advice on crops, soil, fertilizers, and pests. "
            "Mention specific inputs (Urea, DAP, NPK, neem oil) with dosage when relevant. "
            "Structure: context → recommendation → dosage/timing → caution."
            f"{context_note}"
        )},
    ]
    # Pass full conversation history so follow-up questions retain context
    for m in state["messages"]:
        messages.append({"role": m["role"], "content": m["content"]})

    result = await _call_openrouter_text(messages)
    return {**state, "tool_result": result}


async def trusted_vendor_node(state: AgentState) -> AgentState:
    district = state["district"]
    state_name = state["state_name"]

    services = await get_nearby_services(district, state_name)
    if not services:
        return {
            **state,
            "tool_result": (
                f"Adarniya ji, {city} ke aas paas verified services abhi nahi mili. "
                "Main nearby mandi ya agriculture office details se madad kar sakta hoon."
            ),
        }

    messages = [
        {"role": "system", "content": (
            f"{_system_prompt(state)}\n\n"
            f"User location: {city} ({lat}, {lon}).\n"
            f"Nearby trusted services data: {services}\n"
            "Return a concise list with: name, type, distance (km), and phone if available. "
            "Also add one safety note: user should verify by call before visiting."
        )},
        {"role": "user", "content": state["messages"][-1]["content"]},
    ]
    result = await _call_openrouter_text(messages)
    return {**state, "tool_result": result}


async def general_node(state: AgentState) -> AgentState:
    """Handles general knowledge, geography, greetings and off-topic questions.
    Always answers the actual question; remembers conversation context for follow-ups."""
    lang_name = LANG_MAP.get(state["language"], "Hindi")

    has_history = len(state["messages"]) > 1
    context_note = (
        "\nIMPORTANT: Conversation history is provided below. If the user says things like "
        "'firse batao', 'samajh nahi aaya', 'repeat karo', 'again', 'explain more' — "
        "look at the previous answer and re-explain it clearly in simpler terms. Do NOT ask 'what did you want to know?'."
        if has_history else ""
    )

    messages = [
        {"role": "system", "content": (
            f"{_system_prompt(state)}\n\n"
            "TASK: Answer the farmer's question helpfully. "
            "If it's off-topic, answer it correctly then gently offer farming help. "
            "Keep response to 4-5 lines."
            f"{context_note}"
        )},
    ]
    # Pass full conversation so 'explain again' works correctly
    for m in state["messages"]:
        messages.append({"role": m["role"], "content": m["content"]})

    result = await _call_openrouter_text(messages)
    return {**state, "tool_result": result}


async def format_answer(state: AgentState) -> AgentState:
    return {**state, "final_answer": state["tool_result"]}


def _route(state: AgentState) -> str:
    return {
        "weather":        "weather_node",
        "mandi":          "mandi_node",
        "news":           "news_node",
        "scheme":         "news_node",
        "vision":         "llm_node",
        "crop_advice":    "crop_advice_node",
        "trusted_vendor": "trusted_vendor_node",
        "lang_switch":    "lang_switch_node",
        "general":        "general_node",
        "eligibility":    "general_node",
    }.get(state["intent"], "general_node")  # default → general, not llm_node


def _build_agent():
    g = StateGraph(AgentState)
    g.add_node("intent_router",       intent_router)
    g.add_node("weather_node",        weather_node)
    g.add_node("mandi_node",          mandi_node)
    g.add_node("news_node",           news_node)
    g.add_node("llm_node",            llm_node)
    g.add_node("crop_advice_node",    crop_advice_node)
    g.add_node("trusted_vendor_node", trusted_vendor_node)
    g.add_node("lang_switch_node",    lang_switch_node)
    g.add_node("general_node",        general_node)
    g.add_node("format_answer",       format_answer)
    g.set_entry_point("intent_router")
    g.add_conditional_edges("intent_router", _route, {
        "weather_node":        "weather_node",
        "mandi_node":          "mandi_node",
        "news_node":           "news_node",
        "llm_node":            "llm_node",
        "crop_advice_node":    "crop_advice_node",
        "trusted_vendor_node": "trusted_vendor_node",
        "lang_switch_node":    "lang_switch_node",
        "general_node":        "general_node",
    })
    for node in ["weather_node", "mandi_node", "news_node", "llm_node",
                 "crop_advice_node", "trusted_vendor_node", "lang_switch_node", "general_node"]:
        g.add_edge(node, "format_answer")
    g.add_edge("format_answer", END)
    return g.compile()


agent = _build_agent()




