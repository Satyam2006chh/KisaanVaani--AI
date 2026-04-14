from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.config import settings
from app.agents.tools import get_weather, get_mandi_price
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
def get_llm():
    return ChatGroq(
        api_key=settings.groq_api_key,
        model="llama-3.3-70b-versatile",
        temperature=0.4,
        max_tokens=512,
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
    }
    lang_name = lang_map.get(state["language"], "Hindi")

    system = SystemMessage(content=(
        f"Aap KisaanVaani AI hain — Indian farmers ke liye ek helpful AI assistant. "
        f"Hamesha {lang_name} mein jawab dein. "
        f"Simple, clear aur friendly language use karein. "
        f"Sarkari yojanaon (PM Kisan, PMFBY, MSP) ke baare mein accurate jankari dein. "
        f"Jawab 3-4 sentences mein dein, zyada lamba mat karein."
    ))

    history = [
        HumanMessage(content=m["content"]) if m["role"] == "user"
        else AIMessage(content=m["content"])
        for m in state["messages"]
    ]

    llm = get_llm()
    response = await llm.ainvoke([system] + history)
    return {**state, "tool_result": response.content}

# ─── Crop Advice Node ─────────────────────────────────────────
async def crop_advice_node(state: AgentState) -> AgentState:
    """Gives crop recommendation based on location and season."""
    lang_map = {"hi-IN": "Hindi", "pa-IN": "Punjabi", "en-IN": "English"}
    lang_name = lang_map.get(state["language"], "Hindi")

    system = SystemMessage(content=(
        f"Aap ek experienced agriculture expert hain. "
        f"{lang_name} mein jawab dein. "
        f"Farmer {state['district']}, {state['state_name']} mein hain. "
        f"Mausam, mitti aur season ke hisaab se best fasal ki salah dein."
    ))
    llm = get_llm()
    msgs = [HumanMessage(content=state["messages"][-1]["content"])]
    response = await llm.ainvoke([system] + msgs)
    return {**state, "tool_result": response.content}

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
