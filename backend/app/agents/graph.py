import asyncio
import logging
from typing import List, TypedDict

import httpx
from langgraph.graph import END, StateGraph

import google.generativeai as genai
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
    """Specialized call for Multimodal vision using Gemini 1.5 Flash"""
    import google.generativeai as genai
    import base64

    if not settings.gemini_api_key or "your_" in settings.gemini_api_key:
        return "[VISION MOCK] Adarniya Satyam ji, maine aapki fasal ki tasveer ko scan kar liya hai. Yeh 'Leaf Rust' jaisa lag raha hai. Kripya Neem oil ka chhidkaav karein."

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        
        # Strip potential data:image/png;base64, prefix
        if "," in image_base64:
            image_base64 = image_base64.split(",")[1]
            
        img_data = base64.b64decode(image_base64)
        
        # Using the standard SDK pattern for vision
        response = model.generate_content(
            [prompt, {"mime_type": "image/jpeg", "data": img_data}]
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini Vision failed: {e}")
        return "Tasveer analyze karne mein samasya ho rahi hai. Kripya dubara koshish karein."



def _system_prompt(state: AgentState) -> str:
    lang_name = LANG_MAP.get(state["language"], "Hindi")
    supported_langs = ", ".join(LANG_MAP.values())
    
    return (
        f"Aap KisaanVaani AI hain — Indian farmers ke liye ek mahan aur adarniya agricultural expert. "
        f"Aapka kaam kisanon ko sahi, professional aur sammanjanak salah dena hai. "
        f"Aap abhi {state['farmer_name']} ji se baat kar rahe hain jo {state['district']}, {state['state_name']} se hain. "
        f"Hamesha {lang_name} mein jawab dein. "
        f"IMPORTANT: Aap ek multilingual AI hain jo in bhashayon ko samajhta aur bol sakta hai: {supported_langs}. "
        "Agar user aapki capabilities ke bare mein pooche, to garv se batayein ki aap in sabhi bhashayon mein madad kar sakte hain. "
        "\n\nGUIDELINES:\n"
        "1. Samman: Apne har jawab ki shuruat 'Adarniya' ya 'Ji' jaise sammanjanak shabdon se karein.\n"
        "2. Scope: Agar user koi aisa sawal pooche jo kheti ya project se related nahi hai, "
        "to pehle pyaar se bole ki 'Adarniya {state['farmer_name']} ji, ye sawal hamare kheti prashikshan se thoda alag hai, "
        "par aapki jankari ke liye...' aur phir agar aapko jawab pata ho to chhota sa jawab de dein taaki user khush rahe.\n"
        "3. Impact: Aapka jawab impactful aur informative hona chahiye. "
        "Koshish karein ki user ko poori jaankari mile, lekin baatein faltu na hon. "
        "Ek expert scientist ki tarah jawab dein.\n"
        "4. Location Identity: Agar user kisi specific jagah ka naam le (e.g. 'Mumbai ka mausam'), "
        "to us jagah ka data dein. Agar koi jagah mention na ho, tabhi unke registered district ({state['district']}) ka data dein."
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
        "vision": ["kya hai", "bimari", "check", "doctor", "pesticide", "bimari kya hai", "photo", "image"],
        "crop_advice": ["fasal", "crop", "ugao", "kheti", "kya lagao"],
        "news": ["new", "latest", "news", "update", "samachar", "khabar", "taza", "yojana", "scheme", "labh", "benefit", "subsidy"],
        "eligibility": ["eligible", "patrata", "apply", "registration"],
        "lang_switch": ["punjabi", "hindi", "english", "tamil", "gujarati", "bengali", "marathi", "odiya", "kannada", "malayalam", "telugu", "assamese", "bhasha", "language", "mein bolo", "mein jawab do"]
    }
    
    for intent, words in keywords.items():
        if any(w in msg for w in words):
            return {**state, "intent": intent}
            
    # 2. LLM Fallback (Smart)
    intent_prompt = (
        "Classify user intent into: weather, mandi, news, crop_advice, eligibility, scheme, or lang_switch (if user wants to change response language). "
        "Return ONLY the word of the intent.\n\n"
        f"Message: {msg}"
    )
    try:
        raw_intent = await _call_groq([{"role": "system", "content": intent_prompt}], max_tokens=10)
        intent = raw_intent.strip().lower()
    except Exception:
        intent = "scheme"
        
    return {**state, "intent": intent}


async def weather_node(state: AgentState) -> AgentState:
    lang_name = LANG_MAP.get(state["language"], "Hindi")
    user_location = state.get("location")
    
    # 1. Coordinate check for God Level Accuracy
    lat = user_location.get("lat") if user_location else None
    lon = user_location.get("lon") if user_location else None
    
    # 2. Extract city if user asked for a DIFFERENT place
    ext_city = state["district"]
    messages = [
        {"role": "system", "content": (
            "Identify if the user is asking about weather for a specific city OTHER than their current farm. "
            "Return JSON: {'city': 'detected city or null'}. "
            "Return 'null' if they just said 'weather' or 'barsat'."
        )},
        {"role": "user", "content": state["messages"][-1]["content"]},
    ]
    try:
        raw = await _call_groq(messages, max_tokens=30)
        import json
        params = json.loads(raw.strip())
        if params.get("city") and params.get("city") != "null":
            ext_city = params["city"]
            lat, lon = None, None # Reset coords to use city-based geocoding for the other place
    except: pass
    
    # 3. Call tool with higher precision
    weather_data = await get_weather(ext_city, state["state_name"], lat, lon)
    
    # 4. Generate Expert Response
    messages = [
        {"role": "system", "content": (
            f"{_system_prompt(state)}\n\n"
            f"Weather Data: {weather_data}. "
            "Explain in detail including Rain Probability (POP). "
            "If Rain > 70%, warn them very strongly about covering crops. "
            "Jawab itna sateek dein ki lagae aap unke khet mein khade hokar dekh rahe hain."
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
            "Return ONLY a JSON: {'commodity': 'wheat/rice/soybean etc', 'district': 'name'}. "
            "Use only English for JSON keys and values."
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
                "Evaluate the prices. Is it a good time to sell? Mention the trends. "
                f"Explain thoroughly in {lang_name}. Make it feel like an expert market analysis."
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
            "Is news ko kisan ke sawal ke hisaab se summarize karein. "
            "IMPORTANT: Jawab sirf 2-3 sentences mein hona chahiye. Sirf mahatvapoorn baat batayein."
        )},
        {"role": "user", "content": f"Scraped News Content: {raw_content}\n\nFarmer Question: {state['messages'][-1]['content']}"},
    ]
    formatted_result = await _call_groq(messages)
    return {**state, "tool_result": formatted_result}


async def llm_node(state: AgentState) -> AgentState:
    user_msg = state["messages"][-1]["content"]
    
    if state["image_data"]:
        # Vision Path - ULTRA EXPERT SCIENTIST MODE
        prompt = (
            f"SYSTEM ROLE: You are a world-renowned Senior Agri-Scientist and Expert Plant Pathologist. "
            f"The farmer ({state['farmer_name']}) has sent a photo and asked: '{user_msg}'.\n\n"
            "TASK: Analyze this image and generate a professional, high-precision 'SCIENTIFIC CROP HEALTH REPORT'.\n"
            "IMPORTANT: Your identification must be 100% accurate. Do not be generic. Use scientific names.\n\n"
            "REPORT CONTENT (Strictly follow this structure in English):\n"
            "1. IDENTIFICATION: Common Name & *Scientific Name* (Italicized).\n"
            "2. THE CAUSE (WHY IT HAPPENED): Explain the root cause. Did it come from soil? High humidity? Poor ventilation? Nutrient deficiency? Explain scientifically but clearly.\n"
            "3. THE SPREAD (LIFECYCLE): How does this disease spread? (e.g., wind-borne spores, water-splash, or pests like Thrips/Aphids).\n"
            "4. KEY SYMPTOMS: List 3 specific indicators visible in the photo that confirm your diagnosis.\n"
            "5. TREATMENT (IMMEDIATE): Recommend 2 effective chemical treatments with exact dosages (e.g., grams per liter).\n"
            "6. ORGANIC CURE: Provide 1-2 reliable organic or home-made solutions (e.g., Neem, Trichoderma).\n"
            "7. LONG-TERM PREVENTION: 3 practical steps to ensure this never happens again (e.g., Crop rotation, Soil solarization).\n\n"
            "Tone: Authoritative, Professional, and Caring."
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
            f"Respond in {lang_name} professionally. "
            "Jawab itna bada nahi hona chahiye ki user bor ho jaye (MAX 4 sentences)."
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
    g.add_node("lang_switch_node", lang_switch_node)
    g.add_node("format_answer",    format_answer)
    g.set_entry_point("intent_router")
    g.add_conditional_edges("intent_router", _route, {
        "weather_node":     "weather_node",
        "mandi_node":       "mandi_node",
        "news_node":        "news_node",
        "llm_node":         "llm_node",
        "crop_advice_node": "crop_advice_node",
        "lang_switch_node": "lang_switch_node",
    })
    for node in ["weather_node", "mandi_node", "news_node", "llm_node", "crop_advice_node", "lang_switch_node"]:
        g.add_edge(node, "format_answer")
    g.add_edge("format_answer", END)
    return g.compile()


agent = _build_agent()
