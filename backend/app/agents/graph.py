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
    "gu-IN": "Gujarati","od-IN": "Odia",
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
    return (
        f"Aap KisaanVaani AI hain — Indian farmers ke liye ek mahan agricultural expert aur helpful assistant. "
        f"Aapka kaam kisanon ko sahi, vistrit (detailed) aur professional salah dena hai. "
        f"Hamesha {lang_name} mein jawab dein. "
        f"Aap abhi {state['farmer_name']} ji se baat kar rahe hain jo {state['city']}, {state['district']}, {state['state_name']} se hain. "
        f"Apne har jawab ki shuruat samman ke saath karein (e.g. 'Namaste {state['farmer_name']} ji, {state['district']} ke kisanon ke liye ek zaroori jankari...'). "
        "Aapki salah hamesha expert-grade honi chahiye. Sirf upari jankari na dein, balki kisan ko support karne ke liye 'kyun' aur 'kaise' bhi samjhayein. "
        "Sarkari yojanaon (PM Kisan, MSP, PMFBY) ke baare mein hamesha vishwasniya (reliable) aur latest jankari dein. "
        "Farmer ko lage ki koi bada expert unse baat kar raha hai jo unki mitti aur ilake ko samajhta hai."
    )


def intent_router(state: AgentState) -> AgentState:
    msg = state["messages"][-1]["content"].lower()
    if any(w in msg for w in ["mausam", "baarish", "temperature", "rain", "weather", "barsat"]):
        intent = "weather"
    elif any(w in msg for w in ["bhav", "mandi", "rate", "keemat", "price", "daam"]):
        intent = "mandi"
    elif any(w in msg for w in ["fasal", "crop", "ugao", "kheti", "kya lagao"]):
        intent = "crop_advice"
    elif any(w in msg for w in ["new", "latest", "news", "update", "samachar", "khabar", "taza"]):
        intent = "news"
    elif any(w in msg for w in ["eligible", "patrata", "apply", "registration"]):
        intent = "eligibility"
    else:
        intent = "scheme"
    return {**state, "intent": intent}


async def weather_node(state: AgentState) -> AgentState:
    result = await get_weather(state["district"], state["state_name"])
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
            "Is news ko kisan ke sawal ke hisaab se summarize karein aur unhe expert advice ke saath batayein. "
            "Jawab bhot supportive aur accurate hona chahiye."
        )},
        {"role": "user", "content": f"Scraped News Content: {raw_content}\n\nFarmer Question: {state['messages'][-1]['content']}"},
    ]
    formatted_result = await _call_groq(messages)
    return {**state, "tool_result": formatted_result}


async def llm_node(state: AgentState) -> AgentState:
    messages = [
        {"role": "system", "content": (
            f"{_system_prompt(state)}\n\n"
            "Abhi farmer ek general sawal pooch raha hai ya kisi yojana (scheme) ke baare mein jankari chahta hai. "
            "Aapka jawab bhot accurate aur support se bhara hona chahiye. "
            "Agar yojana hai, to patrata (eligibility) aur apply karne ka tarika bhi bataiye. "
            "Apna best expert response dein jo farmer ki madad kare."
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
