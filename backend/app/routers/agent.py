import logging
import re
from fastapi import APIRouter, HTTPException
from app.agents.graph import agent
from app.agents.tools import get_nearest_mandis
from app.config import settings
from app.db.supabase import get_supabase
from app.models.schemas import ChatRequest, ChatResponse
from app.routers.history import save_message
from app.lib.translation import translate_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["Agent"])

_NAME_PATTERNS = [
    re.compile(r"\bmera naam\s+([A-Za-z][A-Za-z\s]{1,40})\s+hai\b", re.IGNORECASE),
    re.compile(r"\bmy name is\s+([A-Za-z][A-Za-z\s]{1,40})\b", re.IGNORECASE),
]


def _extract_name_from_message(message: str) -> str | None:
    if not message:
        return None
    for p in _NAME_PATTERNS:
        m = p.search(message.strip())
        if m:
            name = re.sub(r"\s+", " ", m.group(1)).strip()
            if name and name.lower() not in {"kya", "kaun"}:
                return name[:60]
    return None


def _is_name_recall_question(message: str) -> bool:
    msg = (message or "").lower()
    return (
        "mera naam kya" in msg
        or "mera name kya" in msg
        or ("what is my name" in msg)
        or ("tell me my name" in msg)
    )


@router.post("/mandis/nearby")
async def mandis_nearby(payload: dict):
    lat = payload.get("lat")
    lon = payload.get("lon")
    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="lat and lon are required")
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="lat and lon must be numbers")
    return await get_nearest_mandis(lat_f, lon_f)


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not settings.groq_api_key:
        raise HTTPException(status_code=500, detail="Groq API key not configured")

    sb = get_supabase()
    res = sb.table("users").select("*").eq("phone", req.farmer_id).execute()
    user = res.data[0] if res.data else None

    district   = user.get("district", "") if user else ""
    state_name = user.get("state", "")    if user else ""
    city       = user.get("city", "")     if user else ""
    name       = user.get("name", "Kisaan") if user else "Kisaan"

    # ── Location Handling (Profile Only) ─────────────────────────────
    # Use profile data
    district   = user.get("district", "") if user else ""
    state_name = user.get("state", "")    if user else ""
    city       = user.get("city", "")     if user else ""
    name       = user.get("name", "Kisaan") if user else "Kisaan"

    # Final fallbacks if still empty
    if not district:   district   = "Delhi"
    if not state_name: state_name = "Delhi"
    if not city:       city       = district

    # Prioritize requested language, fallback to profile
    language = req.language if req.language else (user.get("language", "hi-IN") if user else "hi-IN")

    # Explicit memory write from chat: "mera naam X hai" / "my name is X"
    remembered_name = _extract_name_from_message(req.message)
    if remembered_name:
        try:
            sb.table("users").update({"name": remembered_name}).eq("phone", req.farmer_id).execute()
            name = remembered_name
        except Exception as e:
            logger.warning(f"Failed to persist remembered name: {e}")

    # Explicit memory recall shortcut
    if _is_name_recall_question(req.message):
        answer = (
            f"Adarniya ji, aapka naam {name} hai."
            if name and name.strip() and name.strip().lower() != "kisaan"
            else "Adarniya ji, aapne abhi tak naam confirm nahi kiya hai. Kripya boliye: 'Mera naam ... hai'."
        )
        try:
            await save_message(req.farmer_id, req.session_id, "user", req.message)
            await save_message(req.farmer_id, req.session_id, "assistant", answer)
        except Exception as e:
            logger.warning(f"History save failed: {e}")
        return ChatResponse(response=answer, session_id=req.session_id, tool_used="memory")

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
        "messages":         history_msgs + [{"role": "user", "content": agent_message}],
        "farmer_id":        req.farmer_id,
        "farmer_name":      name,
        "language":         language,
        "city":             city,
        "district":         district,
        "state_name":       state_name,
        "intent":           "",
        "tool_result":      "",
        "final_answer":     "",
        "image_data":       req.image,
        "original_message": req.message or "",  # Raw original for follow-up detection
    }

    try:
        result = await agent.ainvoke(initial_state)
        answer = result.get("final_answer", "Kuch galat ho gaya, phir se koshish karein.")
        intent = result.get("intent", "general")
        # NOTE: System prompt already forces output language — no extra translation needed
    except Exception as e:
        logger.exception("Agent error")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    try:
        await save_message(req.farmer_id, req.session_id, "user", req.message)
        await save_message(req.farmer_id, req.session_id, "assistant", answer)
    except Exception as e:
        logger.warning(f"History save failed: {e}")

    return ChatResponse(response=answer, session_id=req.session_id, tool_used=intent)



