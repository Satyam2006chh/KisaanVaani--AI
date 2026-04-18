import logging
from typing import List, TypedDict

import httpx
from langgraph.graph import END, StateGraph

from app.agents.tools import get_mandi_price, get_weather, scrape_agricultural_news
from app.config import settings

logger = logging.getLogger(__name__)

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
        "3. Impact: Aapka jawab chhota aur impactful hona chahiye (MAX 2-3 SENTENCES). "
        "Faltu ki lambi baatein na karein, sirf kaam ki baat aur ek expert tip dein.\n"
        "4. Location Identity: Agar user kisi specific jagah ka naam le (e.g. 'Mumbai ka mausam'), "
        "to us jagah ka data dein. Agar koi jagah mention na ho, tabhi unke registered district ({state['district']}) ka data dein."
    )


async def intent_router(state: AgentState) -> AgentState:
    msg = state["messages"][-1]["content"].lower()
    
    # 1. Primary Keyword match (Very fast)
    keywords = {
        "weather": ["mausam", "mousam", "mosam", "baarish", "rain", "weather", "barsat", "temperature"],
        "mandi": ["bhav", "mandi", "rate", "keemat", "price", "daam"],
        "crop_advice": ["fasal", "crop", "ugao", "kheti", "kya lagao"],
        "news": ["new", "latest", "news", "update", "samachar", "khabar", "taza"],
        "eligibility": ["eligible", "patrata", "apply", "registration"]
    }
    
    for intent, words in keywords.items():
        if any(w in msg for w in words):
            return {**state, "intent": intent}
            
    # 2. LLM Fallback (Smart)
    intent_prompt = (
        "Classify user intent into: weather, mandi, news, crop_advice, eligibility, or scheme. "
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
    msg = state["messages"][-1]["content"]
    
    # Extract district if mentioned
    extraction_prompt = (
        "Aap ek smart data extraction expert hain. Is query se 'district' aur 'state' extract karein. "
        "IMPORTANT: Agar user ne kisi specific shehar ya zila ka naam liya hai (e.g. 'Mumbai', 'Pune', 'New York'), "
        "to use hi 'district' mein rakhein. Agar query mein koi jagah nahi hai, to return empty values. "
        "Return ONLY JSON: {\"district\": \"...\", \"state\": \"...\"}\n\n"
        f"Query: {msg}"
    )
    
    district = state["district"]
    state_name = state["state_name"]
    
    try:
        raw = await _call_groq([{"role": "system", "content": extraction_prompt}], max_tokens=50)
        import json
        params = json.loads(raw)
        if params.get("district"): district = params["district"]
        if params.get("state"): state_name = params["state"]
    except Exception:
        pass

    result = await get_weather(district, state_name)
    return {**state, "tool_result": result}


async def mandi_node(state: AgentState) -> AgentState:
    msg = state["messages"][-1]["content"]
    
    # 1. Use LLM to extract crop and district from natural language
    extraction_prompt = (
        "Aap ek data extraction expert hain. Is message se 'crop' aur 'district' extract karein. "
        "Agar district nahi bataya gaya hai to use empty rakhein. "
        "Fasal (crop) ka naam hamesha English mein dein (e.g. Wheat, Mustard). "
        "Sirf JSON format mein jawab dein: {\"crop\": \"...\", \"district\": \"...\"}\n\n"
        f"Message: {msg}"
    )
    
    try:
        raw_json = await _call_groq([{"role": "system", "content": extraction_prompt}], max_tokens=100)
        import json
        params = json.loads(raw_json)
        crop = params.get("crop", "wheat")
        target_district = params.get("district")
    except Exception:
        # Fallback to simple extraction if LLM fails
        crops = ["gehun", "wheat", "dhan", "rice", "sarson", "mustard", "makka", "maize"]
        crop = next((c for c in crops if c in msg.lower()), "wheat")
        target_district = None

    # Use specified district or fall back to farmer's registered district
    district = target_district if target_district else state["district"]
    state_name = state["state_name"] # We could also extract state but district is usually enough for Mandi
    
    result = await get_mandi_price(crop, district, state_name)
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
    messages = [
        {"role": "system", "content": (
            f"{_system_prompt(state)}\n\n"
            "Abhi farmer ek general sawal pooch raha hai. "
            "IMPORTANT: Jawab bhot chhota aur impactful hona chahiye (MAX 2 sentences)."
        )},
        {"role": "user",   "content": state["messages"][-1]["content"]},
    ]
    result = await _call_groq(messages)
    return {**state, "tool_result": result}


async def crop_advice_node(state: AgentState) -> AgentState:
    lang_name = LANG_MAP.get(state["language"], "Hindi")
    messages = [
        {"role": "system", "content": (
            f"{_system_prompt(state)}\n\n"
            f"Aap ek varishta (senior) agriculture scientist hain. Farmer {state['farmer_name']} ko unke khet ke liye "
            f"sabse behtareen fasal ki salah dein. Unko batayein ki is season mein mitti aur mausam ke hisaab se "
            "kaunsi fasal unhe sabse zyada munafa (profit) degi aur kyun. Fasal ki dekhbhal ke 1-2 expert tips bhi dein."
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
        "crop_advice":"crop_advice_node",
    }.get(state["intent"], "llm_node")


def _build_agent():
    g = StateGraph(AgentState)
    g.add_node("intent_router",    intent_router)
    g.add_node("weather_node",     weather_node)
    g.add_node("mandi_node",       mandi_node)
    g.add_node("news_node",        news_node)
    g.add_node("llm_node",         llm_node)
    g.add_node("crop_advice_node", crop_advice_node)
    g.add_node("format_answer",    format_answer)
    g.set_entry_point("intent_router")
    g.add_conditional_edges("intent_router", _route, {
        "weather_node":     "weather_node",
        "mandi_node":       "mandi_node",
        "news_node":        "news_node",
        "llm_node":         "llm_node",
        "crop_advice_node": "crop_advice_node",
    })
    for node in ["weather_node", "mandi_node", "news_node", "llm_node", "crop_advice_node"]:
        g.add_edge(node, "format_answer")
    g.add_edge("format_answer", END)
    return g.compile()


agent = _build_agent()
