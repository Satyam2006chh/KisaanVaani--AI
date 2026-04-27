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
    messages:     List[dict]
    farmer_id:    str
    farmer_name:  str
    language:     str
    city:         str
    district:     str
    state_name:   str
    intent:       str
    tool_result:  str
    final_answer: str
    image_data:   str # Base64
    location:     dict # {lat, lon, city}


async def _call_groq(messages: list, max_tokens: int = 512) -> str:
    if "your_groq_api_key" in settings.groq_api_key or not settings.groq_api_key:
        print("WARNING: Using mock Groq response because GROQ_API_KEY is not configured.")
        return "[MOCK RESPONSE] Namaste! Main aapka KisaanVaani AI assistant hoon. Main abhi demo mode mein hoon kyunki API keys set nahi hain, lekin main aapki madad karne ke liye taiyaar hoon."

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": messages, "temperature": 0.4, "max_tokens": max_tokens},
        )
    if r.status_code != 200:
        logger.error(f"Groq error {r.status_code}: {r.text[:200]}")
        return "Maaf kijiye, jawab dene mein samasya ho gayi. Dobara koshish karein."
    return r.json()["choices"][0]["message"]["content"]


async def _call_gemini_vision(prompt: str, image_base64: str) -> str:
    """Specialized call for Multimodal vision using Gemini 2.0 Flash.
    Tries multiple models and falls back to Groq text-only on quota exhaustion."""
    import base64 as b64

    if not settings.gemini_api_key or "your_" in settings.gemini_api_key:
        return (
            "Adarniya ji, fasal ki tasveer analyze karne ke liye Gemini API key zaroori hai. "
            "Kripya admin se sampark karein. Aap bina tasveer ke apna sawaal pooch sakte hain."
        )

    # Decode image once
    mime_type = "image/jpeg"
    raw_b64   = image_base64
    if raw_b64.startswith("data:"):
        header, raw_b64 = raw_b64.split(",", 1)
        if "png"  in header: mime_type = "image/png"
        elif "webp" in header: mime_type = "image/webp"
    try:
        img_data = b64.b64decode(raw_b64)
    except Exception as decode_err:
        logger.error(f"Image base64 decode failed: {decode_err}")
        return "Tasveer ka format galat hai. Kripya dobara upload karein."

    # Models to try in order (lite is cheaper on quota)
    MODELS_TO_TRY = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.5-flash"]

    # ── Attempt with new google.genai SDK ───────────────────────────────────
    try:
        from google import genai as new_genai
        from google.genai import types as gtypes

        client = new_genai.Client(api_key=settings.gemini_api_key)
        last_err = None

        for model_name in MODELS_TO_TRY:
            try:
                logger.info(f"Trying Gemini model: {model_name}")
                response = client.models.generate_content(
                    model=model_name,
                    contents=[
                        prompt,
                        gtypes.Part.from_bytes(data=img_data, mime_type=mime_type),
                    ],
                )
                logger.info(f"Gemini {model_name} succeeded")
                return response.text
            except Exception as model_err:
                err_str = str(model_err)
                last_err = err_str
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                    logger.warning(f"Gemini {model_name} quota exhausted — trying next model")
                    continue
                elif "404" in err_str or "NOT_FOUND" in err_str:
                    logger.warning(f"Gemini {model_name} not found — trying next model")
                    continue
                else:
                    logger.error(f"Gemini {model_name} unexpected error: {model_err}")
                    break  # Non-quota error — don't retry other models

        # All models exhausted — fall back to Groq text-only analysis
        logger.warning(f"All Gemini models failed ({last_err[:80]}). Falling back to Groq text analysis.")
        return await _groq_vision_fallback(prompt)

    except ImportError:
        # ── Fallback to old google.generativeai SDK ──────────────────────
        try:
            import google.generativeai as old_genai
            old_genai.configure(api_key=settings.gemini_api_key)
            last_err = None
            for model_name in MODELS_TO_TRY:
                try:
                    model = old_genai.GenerativeModel(model_name)
                    response = model.generate_content(
                        [prompt, {"mime_type": mime_type, "data": img_data}]
                    )
                    return response.text
                except Exception as model_err:
                    err_str = str(model_err)
                    last_err = err_str
                    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                        logger.warning(f"Gemini legacy {model_name} quota — trying next")
                        continue
                    elif "404" in err_str or "NOT_FOUND" in err_str:
                        continue
                    break
            return await _groq_vision_fallback(prompt)
        except Exception as legacy_err:
            logger.error(f"Legacy Gemini SDK failed: {legacy_err}")
            return await _groq_vision_fallback(prompt)

    except Exception as e:
        logger.error(f"Gemini Vision outer exception: {e}")
        return await _groq_vision_fallback(prompt)


async def _groq_vision_fallback(original_prompt: str) -> str:
    """When all Gemini models fail (quota/error), use Groq to give a text-based crop advisory."""
    logger.info("Using Groq text-only fallback for vision query")
    fallback_prompt = (
        "The farmer uploaded a photo of a diseased crop, but image-analysis is temporarily "
        "unavailable (API quota exceeded). Based on the farmer query below, provide a VERY helpful "
        "general crop disease advisory in the farmer's language. "
        "List the 3 most common diseases for typical Indian crops, their visible symptoms, and treatment. "
        "Be specific and actionable.\n\n"
        f"Farmer context:\n{original_prompt[:600]}"
    )
    try:
        result = await _call_groq(
            [{"role": "system", "content": fallback_prompt}],
            max_tokens=450,
        )
        return "[Image AI temporarily unavailable — general disease advice]\n\n" + result
    except Exception as e:
        logger.error(f"Groq vision fallback also failed: {e}")
        return (
            "Adarniya ji, abhi tasveer analyze karne ki suvidha temporarily band hai. "
            "Kripya thodi der baad dobara koshish karein, ya bina tasveer ke apni fasal ki "
            "bimari ka description bolkar poochein — main zaroor madad karunga!"
        )


def _system_prompt(state: AgentState) -> str:
    lang_name = LANG_MAP.get(state["language"], "Hindi")
    supported_langs = ", ".join(LANG_MAP.values())
    
    return (
        "You are KisaanVaani AI, a senior agricultural advisor for Indian farmers.\n"
        f"Current farmer: {state['farmer_name']} from {state['district']}, {state['state_name']}.\n"
        f"Output language lock: You MUST answer only in {lang_name}. Supported languages: {supported_langs}.\n\n"
        "Non-negotiable response rules:\n"
        "1) Respectful tone: Start with a respectful greeting like 'Adarniya ... ji'.\n"
        "2) Data-first: If tool data is provided, prioritize it over assumptions.\n"
        "3) No hallucination: If data is unavailable, say it clearly and suggest next best action.\n"
        "4) Actionable output: End with clear next steps for farmer.\n"
        "5) Brevity with depth: Keep answers concise but practical (typically 3-6 lines).\n"
        "6) Location logic: If user explicitly asks another city, use that city; otherwise use live/current farmer location.\n"
        "7) Safety: Avoid harmful, illegal, or unsafe advice.\n"
        "8) Language purity: Do not switch language mid-answer and do not translate to English unless selected language is English.\n"
        "9) Format quality: Prefer short sections/bullets for readability when giving treatments, dosage, and cautions."
    )


async def intent_router(state: AgentState) -> AgentState:
    msg = state["messages"][-1]["content"].lower()
    
    # 0. VISION PRIORITY: If ANY image data is present, force vision intent
    img = state.get("image_data")
    if img and len(str(img)) > 100: # Check it has content
        return {**state, "intent": "vision"}

    # 1. Primary Keyword match (Very fast)
    keywords = {
        "weather": ["mausam", "mousam", "mosam", "baarish", "rain", "weather", "barsat", "temperature"],
        "mandi": ["bhav", "mandi", "rate", "keemat", "price", "daam"],
        "vision": ["kya hai", "bimari", "check", "pesticide", "bimari kya hai", "photo", "image"],
        "crop_advice": ["fasal", "crop", "ugao", "kheti", "kya lagao"],
        "news": ["new", "latest", "news", "update", "samachar", "khabar", "taza", "yojana", "scheme", "labh", "benefit", "subsidy"],
        "eligibility": ["eligible", "patrata", "apply", "registration"],
        "trusted_vendor": ["vendor", "dealer", "shop", "store", "doctor", "hospital", "clinic", "soil lab", "agri officer", "nearby service", "contact number"],
        "lang_switch": ["punjabi", "hindi", "english", "tamil", "gujarati", "bengali", "marathi", "odiya", "kannada", "malayalam", "telugu", "assamese", "bhasha", "language", "mein bolo", "mein jawab do"]
    }
    
    for intent, words in keywords.items():
        if any(w in msg for w in words):
            return {**state, "intent": intent}
            
    # 2. LLM Fallback (Smart)
    intent_prompt = (
        "Classify user intent into EXACTLY one of these labels: weather, mandi, news, crop_advice, eligibility, scheme, lang_switch. "
        "Return only the label text with no punctuation and no explanation.\n\n"
        f"Message: {msg}"
    )
    try:
        raw_intent = await _call_groq([{"role": "system", "content": intent_prompt}], max_tokens=10)
        intent = raw_intent.strip().lower().replace(".", "").replace("`", "")
        if intent not in {"weather", "mandi", "news", "crop_advice", "eligibility", "scheme", "lang_switch"}:
            intent = "scheme"
    except Exception:
        intent = "scheme"
        
    return {**state, "intent": intent}


async def weather_node(state: AgentState) -> AgentState:
    user_location = state.get("location") or {}

    # PRIMARY: Use live GPS coordinates if available (highest accuracy)
    lat = user_location.get("lat")
    lon = user_location.get("lon")
    # Get the human-readable name of the live location for the AI response
    live_city = user_location.get("city") or user_location.get("name") or state["district"]

    # SECONDARY: Check if user asked about a DIFFERENT city (e.g. "Saharanpur ka mausam batao")
    # If they did, use that city's geocoding instead of live GPS
    messages = [
        {"role": "system", "content": (
            "Identify whether user asked weather for a specific city different from current location. "
            "Return strict JSON only: {\"city\": \"<name>\"} OR {\"city\": null}. "
            "If no explicit different city is mentioned, return null."
        )},
        {"role": "user", "content": state["messages"][-1]["content"]},
    ]
    try:
        raw = await _call_groq(messages, max_tokens=30)
        import json
        params = json.loads(raw.strip())
        asked_city = params.get("city")
        if asked_city and asked_city not in ("null", "None", None, ""):
            # User asked for a different city — use name-based geocoding, ignore live GPS
            weather_data = await get_weather(asked_city, state["state_name"], None, None)
            location_label = asked_city
        else:
            # Use live GPS coordinates for accurate on-farm weather
            weather_data = await get_weather(live_city, state["state_name"], lat, lon)
            location_label = live_city
    except Exception:
        weather_data = await get_weather(live_city, state["state_name"], lat, lon)
        location_label = live_city

    messages = [
        {"role": "system", "content": (
            f"{_system_prompt(state)}\n\n"
            f"Live Location: {location_label}\n"
            f"Weather Data: {weather_data}\n"
            f"Tell farmer clearly that this forecast is for '{location_label}'. "
            "Include: current condition, rain probability, risk level, and 2 concrete farm actions. "
            "If rain probability > 70%, issue a strong crop protection alert."
        )},
        {"role": "user", "content": state["messages"][-1]["content"]},
    ]
    result = await _call_groq(messages)
    return {**state, "tool_result": result}



async def mandi_node(state: AgentState) -> AgentState:
    lang_name = LANG_MAP.get(state["language"], "Hindi")
    messages = [
        {"role": "system", "content": (
            f"Aap ek Mandi Market Analyst hain. User message: {state['messages'][-1]['content']}. "
            f"Extract the crop/commodity. If no district mentioned, assume '{state['district']}'. "
            "Return ONLY strict JSON: {\"commodity\": \"wheat/rice/soybean\", \"district\": \"name\", \"state\": \"name\"}. "
            "Use English keys/values only. No explanation."
        )},
        {"role": "user", "content": state["messages"][-1]["content"]},
    ]
    
    try:
        raw = await _call_groq(messages, max_tokens=50)
        import json
        params = json.loads(raw.strip())
        crop = params.get("commodity", "")
        dist = params.get("district", state["district"])
        st = params.get("state", state["state_name"])
        
        mandi_data = await get_mandi_price(crop, dist, st)
        
        advice_msg = [
            {"role": "system", "content": (
                f"{_system_prompt(state)}\n\n"
                f"Mandi Data for {crop} in {dist}: {mandi_data}. "
                "Evaluate if this is a good sell window. Mention price trend signal and one negotiation tip. "
                "If mandi data is missing, state it explicitly and suggest nearby fallback market query."
            )},
            {"role": "user", "content": state["messages"][-1]["content"]},
        ]
        result = await _call_groq(advice_msg)
    except Exception:
        result = f"Maaf kijiye, {dist} ki mandi mein filhaal data mil nahi raha hai."

    return {**state, "tool_result": result}


async def news_node(state: AgentState) -> AgentState:
    # 1. Scrape raw content via Firecrawl
    raw_content = await scrape_agricultural_news(state["messages"][-1]["content"])
    
    # 2. Pass raw content to AI for professional summarization
    messages = [
        {"role": "system", "content": (
            f"{_system_prompt(state)}\n\n"
            "Aapne internet se yeh taaza news scrape ki hai. "
            "Summarize as: (1) Key update, (2) Farmer impact, (3) What farmer should do now. "
            "Keep it concise and practical."
        )},
        {"role": "user", "content": f"Scraped News Content: {raw_content}\n\nFarmer Question: {state['messages'][-1]['content']}"},
    ]
    formatted_result = await _call_groq(messages)
    return {**state, "tool_result": formatted_result}


async def llm_node(state: AgentState) -> AgentState:
    user_msg = state["messages"][-1]["content"]
    lang_name = LANG_MAP.get(state["language"], "Hindi")
    
    if state["image_data"]:
        # Vision Path - ULTRA EXPERT SCIENTIST MODE
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
        result = await _call_gemini_vision(prompt, state["image_data"])
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
             
        result = await _call_groq(messages)
        
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
            detected = await _call_groq([{"role": "system", "content": prompt}], max_tokens=10)
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
    messages = [
        {"role": "system", "content": (
            f"{_system_prompt(state)}\n\n"
            "Aap ek Agri-Scientist hain. Farmer ko fasal, mitti, keet-nashak (pesticide), ya khad ka expert advice chahiye. "
            "Provide deep technical yet easy to understand tips. Mention specific fertilizer names like Urea, DAP, NPK if relevant. "
            "Give answer in 4 compact parts: diagnosis/context, recommendation, dosage/timing, caution. "
            "Keep it useful and field-ready."
        )},
        {"role": "user", "content": state["messages"][-1]["content"]},
    ]
    result = await _call_groq(messages)
    return {**state, "tool_result": result}


async def trusted_vendor_node(state: AgentState) -> AgentState:
    loc = state.get("location") or {}
    lat = loc.get("lat")
    lon = loc.get("lon")
    city = loc.get("city") or state.get("city")

    if lat is None or lon is None:
        return {
            **state,
            "tool_result": (
                "Adarniya ji, trusted vendor/doctor dhoondhne ke liye live location required hai. "
                "Kripya location permission allow karke phir se poochiye."
            ),
        }

    services = await get_nearby_services(float(lat), float(lon))
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
    result = await _call_groq(messages)
    return {**state, "tool_result": result}


async def format_answer(state: AgentState) -> AgentState:
    return {**state, "final_answer": state["tool_result"]}


def _route(state: AgentState) -> str:
    return {
        "weather":    "weather_node",
        "mandi":      "mandi_node",
        "news":       "news_node",
        "scheme":     "news_node",
        "vision":     "llm_node",
        "crop_advice":"crop_advice_node",
        "trusted_vendor":"trusted_vendor_node",
        "lang_switch":"lang_switch_node",
    }.get(state["intent"], "llm_node")


def _build_agent():
    g = StateGraph(AgentState)
    g.add_node("intent_router",    intent_router)
    g.add_node("weather_node",     weather_node)
    g.add_node("mandi_node",       mandi_node)
    g.add_node("news_node",        news_node)
    g.add_node("llm_node",         llm_node)
    g.add_node("crop_advice_node", crop_advice_node)
    g.add_node("trusted_vendor_node", trusted_vendor_node)
    g.add_node("lang_switch_node", lang_switch_node)
    g.add_node("format_answer",    format_answer)
    g.set_entry_point("intent_router")
    g.add_conditional_edges("intent_router", _route, {
        "weather_node":     "weather_node",
        "mandi_node":       "mandi_node",
        "news_node":        "news_node",
        "llm_node":         "llm_node",
        "crop_advice_node": "crop_advice_node",
        "trusted_vendor_node": "trusted_vendor_node",
        "lang_switch_node": "lang_switch_node",
    })
    for node in ["weather_node", "mandi_node", "news_node", "llm_node", "crop_advice_node", "trusted_vendor_node", "lang_switch_node"]:
        g.add_edge(node, "format_answer")
    g.add_edge("format_answer", END)
    return g.compile()


agent = _build_agent()
