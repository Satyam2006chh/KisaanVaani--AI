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
        f"Aap KisaanVaani AI hain — Indian farmers ke liye ek helpful AI assistant. "
        f"Hamesha {lang_name} mein jawab dein. Simple aur friendly language use karein. "
        f"Aap abhi {state['farmer_name']} se baat kar rahe hain jo {state['city']}, {state['district']}, {state['state_name']} se hain. "
        f"Unka naam lekar unka swagat karein (e.g. 'Namaste {state['farmer_name']} ji'). "
        f"Sarkari yojanaon (PM Kisan, PMFBY, MSP) ke baare mein accurate jankari dein. "
        f"Jawab 3-4 sentences mein dein."
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
    msg = state["messages"][-1]["content"].lower()
    crops = ["gehun", "wheat", "dhan", "rice", "sarson", "mustard",
             "makka", "maize", "bajra", "jowar", "cotton", "kapas",
             "chana", "gram", "moong", "urad", "masoor", "ganna"]
    crop = next((c for c in crops if c in msg), "wheat")
    result = await get_mandi_price(crop, state["district"], state["state_name"])
    return {**state, "tool_result": result}


async def news_node(state: AgentState) -> AgentState:
    result = await scrape_agricultural_news(state["messages"][-1]["content"])
    return {**state, "tool_result": result}


async def llm_node(state: AgentState) -> AgentState:
    messages = [
        {"role": "system", "content": _system_prompt(state)},
        {"role": "user",   "content": state["messages"][-1]["content"]},
    ]
    result = await _call_groq(messages)
    return {**state, "tool_result": result}


async def crop_advice_node(state: AgentState) -> AgentState:
    lang_name = LANG_MAP.get(state["language"], "Hindi")
    messages = [
        {"role": "system", "content": (
            f"Aap ek experienced agriculture expert hain. Hamesha {lang_name} mein jawab dein. "
            f"Farmer {state['farmer_name']} {state['city']}, {state['state_name']} mein rehta hai. "
            f"Season aur mitti ke hisaab se best fasal ki salah dein. Jawab 3-4 sentences mein."
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
