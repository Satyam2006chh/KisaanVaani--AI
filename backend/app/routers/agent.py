import logging

from fastapi import APIRouter, HTTPException

from app.agents.graph import agent
from app.config import settings
from app.db.mongo import get_db
from app.models.schemas import ChatRequest, ChatResponse
from app.routers.history import save_message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["Agent"])


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not settings.groq_api_key:
        raise HTTPException(status_code=500, detail="Groq API key not configured")

    db = get_db()
    user = await db["users"].find_one({"phone": req.farmer_id})

    district   = user.get("district", "Delhi") if user else "Delhi"
    state_name = user.get("state", "Delhi")    if user else "Delhi"
    language   = user.get("language", req.language) if user else req.language

    initial_state = {
        "messages":     [{"role": "user", "content": req.message}],
        "farmer_id":    req.farmer_id,
        "language":     language,
        "district":     district,
        "state_name":   state_name,
        "intent":       "",
        "tool_result":  "",
        "final_answer": "",
    }

    try:
        result = await agent.ainvoke(initial_state)
        answer = result.get("final_answer", "Kuch gadbad ho gayi, dobara koshish karein.")
        intent = result.get("intent", "general")
    except Exception as e:
        logger.exception("Agent error")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    try:
        await save_message(req.farmer_id, req.session_id, "user", req.message)
        await save_message(req.farmer_id, req.session_id, "assistant", answer)
    except Exception as e:
        logger.warning(f"History save failed: {e}")

    return ChatResponse(response=answer, session_id=req.session_id, tool_used=intent)
