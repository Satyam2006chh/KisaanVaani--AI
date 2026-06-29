import asyncio
import logging
from typing import List, TypedDict

import httpx
from langgraph.graph import END, StateGraph

from app.agents.tools import get_mandi_price, get_weather, scrape_agricultural_news
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


TEXT_MODELS = [
    "google/gemini-2.5-flash",             # Extremely fast, highly accurate, and very cost-effective
    "anthropic/claude-3.5-sonnet",         # Very smart, moderate speed
    "deepseek/deepseek-r1",                # Reasoning model, highest latency
    "openai/gpt-4o",                       # Premium high stability
]

VISION_MODELS = [
    "google/gemini-2.5-flash",             # Extremely fast, highly accurate, and very cost-effective
    "openai/gpt-4o",                       # Premium high stability
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

    city     = _clean_location(state.get("city", ""))
    district = _clean_location(state.get("district", ""))
    st       = _clean_location(state.get("state_name", ""))
    
    loc_parts = [p for p in [city, district, st] if p]
    seen = set()
    unique_parts = [x for x in loc_parts if not (x in seen or seen.add(x))]
    loc_str  = ", ".join(unique_parts) if unique_parts else "India"

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
        "1. EXACT DIRECT ANSWER ONLY: Give the exact answer immediately. DO NOT add conversational filler like 'Here is the translation', 'Sure', or 'I can help'.\n"
        "2. MAXIMUM CONCISENESS: For translations or simple questions, provide ONLY the requested text. DO NOT explain grammar, DO NOT provide alternatives, and NEVER ask follow-up questions (e.g. 'Do you want to know more?').\n"
        "3. NO MARKDOWN: Never use symbols like *, **, #, or _ in your final response. Keep text plain and natural.\n"
        "4. NO FILLER: Avoid generic sentences like 'I hope this is helpful' or 'Please contact me for more'. Be professional.\n"
        "5. Complete your answer fully — never stop mid-sentence.\n"
        "6. Safety — no harmful or dangerous advice.\n"
    ).replace("{name}", name)



async def intent_router(state: AgentState) -> AgentState:
    msg = state["messages"][-1]["content"].strip()
    
    # Construct conversation history for context
    history_text = ""
    if len(state["messages"]) > 1:
        history_text = "CONVERSATION HISTORY:\n"
        for m in state["messages"][:-1]:
            role = "Farmer" if m["role"] == "user" else "AI"
            history_text += f"{role}: {m['content']}\n"
    
    # Strong, Context-Aware LLM Router Prompt
    router_prompt = (
        "You are the MASTER ROUTER for KisaanVaani, an AI assistant for Indian farmers.\n"
        "You have full knowledge of the entire system architecture. Your job is to assign the farmer's question to the EXACT CORRECT NODE.\n"
        "If you route incorrectly, the whole system will fail.\n\n"
        "AVAILABLE NODES AND THEIR KNOWLEDGE:\n"
        "1. weather      -> Use this for ANY questions about rain, temperature, forecast, or weather conditions.\n"
        "2. mandi        -> Use this for ANY questions about market rates, crop prices, bhav, or selling prices.\n"
        "3. vision       -> Use this ONLY if the farmer explicitly asks you to look at a photo/image/picture to diagnose a disease.\n"
        "4. crop_advice  -> Use this for ANY questions about farming techniques, fertilizers, pests, seeds, diseases (without photo), or crop care.\n"
        "5. news         -> Use this for ANY questions about Government Schemes (Yojna), subsidies, PM Kisan, agri news, or loans.\n"
        "6. lang_switch  -> Use this ONLY if the farmer asks to change the language (e.g., 'Speak in Punjabi', 'Hindi me bolo').\n"
        "7. general      -> Use this for geography, greetings (hello, namaste), 'who are you', or off-topic non-farming questions.\n\n"
        f"{history_text}\n"
        f"LATEST FARMER MESSAGE: {msg}\n\n"
        "CRITICAL RULE FOR FOLLOW-UPS: If the latest message is a follow-up (e.g., 'explain again', 'firse batao', 'aur batao'), you MUST route it to the SAME node as the previous topic discussed in the history.\n\n"
        "OUTPUT FORMAT: Return ONLY the exact node name (e.g., 'weather' or 'mandi'). Do NOT output any other text or punctuation."
    )
    
    try:
        raw_intent = await _call_openrouter_text([{"role": "system", "content": router_prompt}], max_tokens=15)
        intent = raw_intent.strip().lower().replace(".", "").replace("`", "").replace("'", "").split()[0]
        
        valid_intents = {"weather", "mandi", "vision", "crop_advice", "news", "lang_switch", "general"}
        if intent not in valid_intents:
            logger.warning(f"Router returned invalid intent '{intent}', falling back to general.")
            intent = "general"
    except Exception as e:
        logger.error(f"LLM Router failed: {e}. Falling back to general.")
        intent = "general"
        
    logger.info(f"LLM Router assigned intent: {intent}")
    return {**state, "intent": intent}



async def _extract_location_or_fallback(user_msg: str, original_msg: str, profile_district: str, profile_state: str) -> tuple[str, str]:
    """
    Extracts District/City and State from the user message, falling back to profile location if not specified.
    """
    prompt = (
        "You are an expert geographical location extractor for Indian agriculture.\n"
        f"Farmer Profile Location: District/Mandi='{profile_district}', State='{profile_state}'.\n\n"
        "From the user query (provided in both translated English and original language), extract the target location "
        "the user is asking about (District/City/Tehsil/Mandi and State).\n\n"
        "Rules:\n"
        "1. If the user mentions a specific district, city, town, tehsil, or mandi (e.g. 'Jaipur', 'Patiala', 'Ludhiana', 'Azadpur', 'Bilaspur'), "
        "extract it as 'district'. Always return the clean proper name in English.\n"
        "2. If the user mentions a specific state (e.g. 'Rajasthan', 'Punjab', 'Uttar Pradesh'), extract it as 'state'. Always return the clean proper name in English.\n"
        "3. If the user asks about their own area ('mere yahan', 'apne yahan', 'my district', 'my state', 'local', etc.) or does NOT specify any location, "
        "fall back to the profile's district and state.\n"
        "4. If a district/city is specified but state is missing, try to infer the correct state based on well-known geography (e.g., 'Jaipur' -> 'Rajasthan', 'Patiala' -> 'Punjab', 'Ludhiana' -> 'Punjab', 'Karnal' -> 'Haryana', 'Azadpur' -> 'Delhi'), "
        "otherwise use the profile's state.\n"
        "5. Ignore generic words like 'mandi', 'mausam', 'weather', 'bhav', etc. as locations.\n\n"
        "Return ONLY a valid JSON object in this format:\n"
        "{\"district\": \"<extracted or fallback district>\", \"state\": \"<extracted or fallback state>\"}\n"
        "Do not include any explanation or markdown formatting.\n\n"
        f"Translated English Query: \"{user_msg}\"\n"
        f"Original Query: \"{original_msg}\""
    )
    dist = profile_district
    st = profile_state
    try:
        raw = await _call_openrouter_text([{"role": "system", "content": prompt}], max_tokens=60)
        clean = raw.strip().strip("```json").strip("```").strip()
        import json
        params = json.loads(clean)
        extracted_dist = _clean_location(params.get("district", dist))
        extracted_st = _clean_location(params.get("state", st))
        if extracted_dist and extracted_dist.lower() not in ("null", "none", "n/a", "na", ""):
            dist = extracted_dist
        if extracted_st and extracted_st.lower() not in ("null", "none", "n/a", "na", ""):
            st = extracted_st
    except Exception as e:
        logger.warning(f"Location extraction failed: {e}. Using profile location.")
    
    return dist, st


async def weather_node(state: AgentState) -> AgentState:
    user_msg = state["messages"][-1]["content"]
    original_msg = state.get("original_message", "")
    profile_district = _clean_location(state.get("district", "")) or "Delhi"
    profile_state    = _clean_location(state.get("state_name", "")) or "Delhi"

    dist, st = await _extract_location_or_fallback(user_msg, original_msg, profile_district, profile_state)
    weather_data = await get_weather(dist, st)
    
    overridden_state = {**state, "district": dist, "state_name": st}

    messages = [
        {"role": "system", "content": (
            f"{_system_prompt(overridden_state)}\n\n"
            f"Location: {dist}, {st}\n"
            f"PROCESSED WEATHER INTELLIGENCE JSON: {weather_data}\n\n"
            "TASK: Act as an expert agricultural advisor. You have received processed weather intelligence JSON.\n"
            "Analyze the data and give simple, actionable advice to the farmer in their selected language.\n"
            "RULES:\n"
            "1. DO NOT use heavy technical words (like evapotranspiration, UV index, humidity percentages). Speak like a helpful local farmer.\n"
            "2. Tell them EXACTLY what to do today and tomorrow (e.g., 'Aaj khet mein dawai na chhidkein kyunki hawa tez hai').\n"
            "3. Mention if irrigation is needed based on the JSON.\n"
            "4. Warn them about fungal disease or heat/wind risk if the JSON says High or Medium.\n"
            "5. Do NOT invent or calculate fake data. Only rely on the JSON provided.\n"
            "6. Keep it conversational, caring, and highly practical."
        )},
    ]
    for m in state["messages"]:
        messages.append({"role": m["role"], "content": m["content"]})
    result = await _call_openrouter_text(messages)
    return {**state, "tool_result": result}



async def mandi_node(state: AgentState) -> AgentState:
    import json

    user_msg   = state["messages"][-1]["content"]
    original_msg = state.get("original_message", "")
    profile_district = _clean_location(state.get("district", "")) or "Delhi"
    profile_state    = _clean_location(state.get("state_name", "")) or "Delhi"

    # Step 1: Use LLM to extract crop + target district from the user's message
    extract_prompt = (
        "You are a mandi price analyst for Indian agriculture.\n"
        f"Farmer profile: district='{profile_district}', state='{profile_state}'.\n\n"
        "From the user message below (both translated and original), extract:\n"
        "  - commodity : the crop/commodity in English (e.g. wheat, rice, sarson, soybean)\n"
        "  - district  : the mandi/district the user is asking about.\n"
        "    * If user says 'mere zile' / 'apne ilake' / 'my district' / no specific place → use the profile district above.\n"
        "    * If user names a specific mandi or city (e.g. 'Azadpur', 'Ludhiana', 'Karnal') → use that.\n"
        "  - state     : the state the district belongs to. Use profile state if unknown.\n\n"
        "Return ONLY valid JSON like: {\"commodity\": \"wheat\", \"district\": \"Patiala\", \"state\": \"Punjab\"}\n"
        "No explanation. No markdown.\n\n"
        f"Translated English Query: \"{user_msg}\"\n"
        f"Original Query: \"{original_msg}\""
    )

    dist = profile_district
    st   = profile_state
    crop = "wheat"
    try:
        raw  = await _call_openrouter_text([{"role": "system", "content": extract_prompt}], max_tokens=60)
        clean = raw.strip().strip("```json").strip("```").strip()
        params = json.loads(clean)
        crop = params.get("commodity", crop).lower().strip()
        extracted_dist = _clean_location(params.get("district", dist))
        extracted_st   = _clean_location(params.get("state", st))
        if extracted_dist and extracted_dist.lower() not in ("null", "none", "n/a", "na", ""):
            dist = extracted_dist
        if extracted_st and extracted_st.lower() not in ("null", "none", "n/a", "na", ""):
            st = extracted_st
    except Exception as parse_err:
        logger.warning(f"Mandi param extraction failed: {parse_err} | raw='{raw[:80]}'")

    # Step 2: Fetch mandi price data
    mandi_data = await get_mandi_price(crop, dist, st)

    # Step 3: Compose final answer using overridden location
    overridden_state = {**state, "district": dist, "state_name": st}
    advice_msg = [
        {"role": "system", "content": (
            f"{_system_prompt(overridden_state)}\n\n"
            f"MANDI DATA — {crop.title()} in {dist}, {st}:\n{mandi_data}\n\n"
            "TASK: Give a clear, practical mandi price report to the farmer.\n"
            "Include: (a) current price / MSP reference, (b) whether it's a good time to sell, "
            "(c) one negotiation tip.\n"
            "CRITICAL: If the live MANDI DATA above is missing or empty, provide the approximate minimum support price (MSP) for the crop as a reference, and give general market trends for it."
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
    # Use English translated message for scraping (gives 100x better results on search engines)
    search_query = state["messages"][-1]["content"]
    # Keep original question for the prompt context
    user_question = state.get("original_message") or search_query

    # 1. Scrape live content
    raw_content = await scrape_agricultural_news(search_query)

    # 2. Compose answer using ONLY scraped data
    messages = [
        {"role": "system", "content": (
            f"{_system_prompt(state)}\n\n"
            "You are an expert on Indian agricultural government schemes and policies.\n"
            f"FARMER'S QUESTION: {user_question}\n\n"
            "Use the LIVE information below to give a COMPLETE, SPECIFIC answer:\n"
            f"--- LIVE SCRAPED DATA ---\n{raw_content[:2000]}\n\n"
            "TASK: Give a highly structured, professional answer based on the user's question, exactly like a News Anchor or a Premium AI Overview.\n"
            "FORMATTING RULES (Use emojis like ✅, 👉 instead of Markdown asterisks/hash):\n"
            "1. Start with a clear headline summarizing the top news.\n"
            "2. Break down the information into neat, easy-to-read points.\n"
            "3. If the user asks about a GOVERNMENT SCHEME, extract the Exact Scheme Name, Eligibility, and Application Process from the LIVE SCRAPED DATA.\n"
            "4. STRICT RULE: You MUST rely ONLY on the LIVE SCRAPED DATA provided above. Do not use your own pre-trained knowledge to hallucinate schemes that are not in the scraped data.\n"
            "5. If the LIVE SCRAPED DATA is completely empty or completely irrelevant to the question, politely inform the user that live news/data is currently unavailable for their query.\n"
            f"Answer completely in {lang_name}. Be extremely specific, detailed, and professional."
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
        "lang_switch_node":    "lang_switch_node",
        "general_node":        "general_node",
    })
    for node in ["weather_node", "mandi_node", "news_node", "llm_node",
                 "crop_advice_node", "lang_switch_node", "general_node"]:
        g.add_edge(node, "format_answer")
    g.add_edge("format_answer", END)
    return g.compile()


agent = _build_agent()




