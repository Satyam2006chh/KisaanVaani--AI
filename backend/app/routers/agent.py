import logging
from fastapi import APIRouter, HTTPException
from app.agents.graph import agent
from app.config import settings
from app.db.supabase import get_supabase
from app.models.schemas import ChatRequest, ChatResponse
from app.routers.history import save_message
from app.lib.translation import translate_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["Agent"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not settings.groq_api_key:
        raise HTTPException(status_code=500, detail="Groq API key not configured")

    sb = get_supabase()
    res = sb.table("users").select("*").eq("phone", req.farmer_id).execute()
    user = res.data[0] if res.data else None

    district   = user.get("district", "Delhi") if user else "Delhi"
    state_name = user.get("state", "Delhi")    if user else "Delhi"
    city       = user.get("city", district)    if user else district
    name       = user.get("name", "Kisaan")    if user else "Kisaan"
    language   = user.get("language", req.language) if user else req.language

    # Multilingual Flow: AI works in English
    agent_message = req.english_message
    if not agent_message:
        agent_message = await translate_text(req.message, language, "en-IN")

    initial_state = {
        "messages":     [{"role": "user", "content": agent_message}],
        "farmer_id":    req.farmer_id,
        "farmer_name":  name,
        "language":     "en-IN", # Force Agent to English
        "city":         city,
        "district":     district,
        "state_name":   state_name,
        "intent":       "",
        "tool_result":  "",
        "final_answer": "",
    }

    try:
        result = await agent.ainvoke(initial_state)
        answer_en = result.get("final_answer", "Something went wrong, please try again.")
        intent = result.get("intent", "general")
        
        # Translate back to User Language
        answer = await translate_text(answer_en, "en-IN", language)
    except Exception as e:
        logger.exception("Agent error")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    try:
        await save_message(req.farmer_id, req.session_id, "user", req.message)
        await save_message(req.farmer_id, req.session_id, "assistant", answer)
    except Exception as e:
        logger.warning(f"History save failed: {e}")

    return ChatResponse(response=answer, session_id=req.session_id, tool_used=intent)
