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

    # LATEST LIVE LOCATION OVERRIDE (CRITICAL FOR ACCURACY)
    if req.location and isinstance(req.location, dict):
        live_dist = req.location.get("place") or req.location.get("district")
        live_state = req.location.get("state")
        live_city = req.location.get("city")
        if live_dist: district = live_dist
        if live_state: state_name = live_state
        if live_city: city = live_city
    # Prioritize requested/detected language for dynamic response, fallback to profile
    language = req.language if req.language else (user.get("language", "hi-IN") if user else "hi-IN")

    # Multilingual Flow: AI works in English
    agent_message = req.english_message
    if not agent_message:
        agent_message = await translate_text(req.message, language, "en-IN")

    # LOAD SESSION HISTORY (Memory)
    history_msgs = []
    try:
        hist_res = sb.table("messages").select("role", "content")\
            .eq("farmer_id", req.farmer_id)\
            .eq("session_id", req.session_id)\
            .order("timestamp", desc=True).limit(10).execute()
        
        # Reverse to get chronological order
        for m in reversed(hist_res.data or []):
            role = "user" if m["role"] == "user" else "assistant"
            history_msgs.append({"role": role, "content": m["content"]})
    except Exception as e:
        logger.warning(f"Failed to load history context: {e}")

    initial_state = {
        "messages":     history_msgs + [{"role": "user", "content": agent_message}],
        "farmer_id":    req.farmer_id,
        "farmer_name":  name,
        "language":     language,
        "city":         city,
        "district":     district,
        "state_name":   state_name,
        "intent":       "",
        "tool_result":  "",
        "final_answer": "",
        "image_data":   req.image,
        "location":     req.location, # Rajpura Coords passed here
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


@router.post("/mandis/nearby")
async def nearby_mandis(req: dict):
    lat = req.get("lat")
    lon = req.get("lon")
    if lat is None or lon is None:
        return []
    
    from app.agents.tools import get_nearest_mandis, get_mandi_price
    mandis = await get_nearest_mandis(float(lat), float(lon))
    
    # Fetch real rates for each nearby mandi in parallel to save time
    import asyncio
    async def _fill_rate(m):
        try:
            m["rate_info"] = await get_mandi_price("Wheat", m["name"], m["state"])
        except:
            m["rate_info"] = None

    try:
        await asyncio.wait_for(asyncio.gather(*[_fill_rate(m) for m in mandis]), timeout=5.0)
    except asyncio.TimeoutError:
        logger.warning("Mandi price fetch timed out")
    
    return mandis
