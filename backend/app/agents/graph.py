from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from app.config import settings
from app.agents.tools import get_weather, get_mandi_price
import httpx
import re

# ─── State ────────────────────────────────────────────────────
class AgentState(TypedDict):
    messages:    List[dict]
    farmer_id:   str
    language:    str
    district:    str
    state_name:  str
    intent:      str
    tool_result: str
    final_answer:str

# ─── LLM ─────────────────────────────────────────────────────
async def call_groq(messages: list, temperature: float = 0.4, max_tokens: int = 512) -> str:
    """Call Groq API directly using httpx (avoids langchain-groq bugs)."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.groq_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        error_text = response.text
        print(f"[Groq API Error] {response.status_code}: {error_text}")
        return "Maaf kijiye, jawab dene mein samasya ho gayi. Kripya dobara koshish karein."

    data = response.json()
    return data["choices"][0]["message"]["content"]

def build_system_prompt(lang_name: str, district: str, state: str) -> str:
    """Build system prompt for the AI."""
    return (
        f"Aap KisaanVaani AI hain — Indian farmers ke liye ek helpful AI assistant. "
        f"Hamesha {lang_name} mein jawab dein. "
        f"Simple, clear aur friendly language use karein. "
        f"Farmer {district}, {state} mein rehta hai. "
        f"Sarkari yojanaon (PM Kisan, PMFBY, MSP) ke baare mein accurate jankari dein. "
        f"Jawab 3-4 sentences mein dein, zyada lamba mat karein."
    )

# ─── Intent Detection Node ────────────────────────────────────
def intent_router(state: AgentState) -> AgentState:
    """Classify the user query into one of 5 intents."""
    last_msg = state["messages"][-1]["content"].lower()

    if any(w in last_msg for w in ["mausam", "baarish", "temperature", "rain", "weather", "barsat"]):
        intent = "weather"
    elif any(w in last_msg for w in ["bhav", "mandi", "rate", "keemat", "price", "daam"]):
        intent = "mandi"
    elif any(w in last_msg for w in ["eligible", "patrata", "qualification", "apply", "registration"]):
        intent = "eligibility"
    elif any(w in last_msg for w in ["fasal", "crop", "ugao", "kheti", "kya lagao"]):
        intent = "crop_advice"
    else:
        intent = "scheme"   # default → RAG

    return {**state, "intent": intent}

# ─── Weather Node ─────────────────────────────────────────────
async def weather_node(state: AgentState) -> AgentState:
    result = await get_weather(state["district"], state["state_name"])
    return {**state, "tool_result": result}

# ─── Mandi Node ───────────────────────────────────────────────
async def mandi_node(state: AgentState) -> AgentState:
    last_msg = state["messages"][-1]["content"]
    # Simple crop extraction — improve with NLP later
    crops = ["gehun", "wheat", "dhan", "rice", "sarson", "mustard",
             "makka", "maize", "bajra", "jowar", "cotton", "kapas"]
    crop = next((c for c in crops if c in last_msg.lower()), "wheat")
    result = await get_mandi_price(crop, state["district"])
    return {**state, "tool_result": result}

# ─── Scheme/General LLM Node ──────────────────────────────────
async def llm_node(state: AgentState) -> AgentState:
    """Handles scheme queries and general farming questions via Groq."""
    lang_map = {
        "hi-IN": "Hindi", "pa-IN": "Punjabi", "bn-IN": "Bengali",
        "ta-IN": "Tamil",  "te-IN": "Telugu",  "en-IN": "English",
        "kn-IN": "Kannada", "ml-IN": "Malayalam", "mr-IN": "Marathi",
        "gu-IN": "Gujarati", "od-IN": "Odia",
    }
    lang_name = lang_map.get(state["language"], "Hindi")

    messages = [
        {"role": "system", "content": build_system_prompt(lang_name, state["district"], state["state_name"])},
        {"role": "user", "content": state["messages"][-1]["content"]}
    ]

    response = await call_groq(messages)
    return {**state, "tool_result": response}

# ─── Crop Advice Node ─────────────────────────────────────────
async def crop_advice_node(state: AgentState) -> AgentState:
    """Gives crop recommendation based on location and season."""
    lang_map = {"hi-IN": "Hindi", "pa-IN": "Punjabi", "en-IN": "English",
                 "bn-IN": "Bengali", "ta-IN": "Tamil", "te-IN": "Telugu"}
    lang_name = lang_map.get(state["language"], "Hindi")

    messages = [
        {"role": "system", "content": (
            f"Aap ek experienced agriculture expert hain. "
            f"Hamesha {lang_name} mein jawab dein. "
            f"Farmer {state['district']}, {state['state_name']} mein rehta hai. "
            f"Mausam, mitti aur season ke hisaab se best fasal ki salah dein. "
            f"Jawab 3-4 sentences mein dein."
        )},
        {"role": "user", "content": state["messages"][-1]["content"]}
    ]

    response = await call_groq(messages)
    return {**state, "tool_result": response}

# ─── Format Final Answer ──────────────────────────────────────
async def format_answer(state: AgentState) -> AgentState:
    """Final formatting — combine tool result as the answer."""
    return {**state, "final_answer": state["tool_result"]}

# ─── Routing Logic ────────────────────────────────────────────
def route_intent(state: AgentState) -> str:
    routes = {
        "weather":    "weather_node",
        "mandi":      "mandi_node",
        "crop_advice":"crop_advice_node",
        "eligibility":"llm_node",
        "scheme":     "llm_node",
    }
    return routes.get(state["intent"], "llm_node")

# ─── Build Graph ──────────────────────────────────────────────
def build_agent():
    graph = StateGraph(AgentState)

    graph.add_node("intent_router",    intent_router)
    graph.add_node("weather_node",     weather_node)
    graph.add_node("mandi_node",       mandi_node)
    graph.add_node("llm_node",         llm_node)
    graph.add_node("crop_advice_node", crop_advice_node)
    graph.add_node("format_answer",    format_answer)

    graph.set_entry_point("intent_router")

    graph.add_conditional_edges("intent_router", route_intent, {
        "weather_node":     "weather_node",
        "mandi_node":       "mandi_node",
        "llm_node":         "llm_node",
        "crop_advice_node": "crop_advice_node",
    })

    for node in ["weather_node", "mandi_node", "llm_node", "crop_advice_node"]:
        graph.add_edge(node, "format_answer")

    graph.add_edge("format_answer", END)

    return graph.compile()

# Singleton agent instance
agent = build_agent()
