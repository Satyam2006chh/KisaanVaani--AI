from fastapi import APIRouter, HTTPException
from app.models.schemas import ChatRequest, ChatResponse
from app.agents.graph import agent
from app.routers.history import save_message
import uuid

router = APIRouter(prefix="/api/agent", tags=["Agent"])

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Main chat endpoint:
    1. Takes transcribed text from frontend
    2. Runs through LangGraph agent
    3. Returns Hindi/regional language response
    4. Saves both messages to MongoDB
    """
    # Build messages list (can include history for multi-turn later)
    messages = [{"role": "user", "content": req.message}]

    # Initial state for LangGraph
    initial_state = {
        "messages":    messages,
        "farmer_id":   req.farmer_id,
        "language":    req.language,
        "district":    "Delhi",      # TODO: fetch from user profile
        "state_name":  "Delhi",      # TODO: fetch from user profile
        "intent":      "",
        "tool_result": "",
        "final_answer":"",
    }

    try:
        result = await agent.ainvoke(initial_state)
        answer = result.get("final_answer", "Kuch gadbad ho gayi, dobara koshish karein.")
        intent = result.get("intent", "general")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    # Save to MongoDB history
    await save_message(req.farmer_id, req.session_id, "user",      req.message)
    await save_message(req.farmer_id, req.session_id, "assistant", answer)

    return ChatResponse(
        response=answer,
        session_id=req.session_id,
        tool_used=intent,
    )
