import logging
import re
from fastapi import APIRouter, HTTPException
from app.agents.graph import agent
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


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not settings.openrouter_api_key or "your_" in settings.openrouter_api_key:
        logger.warning("OpenRouter API key not configured. Returning graceful sandbox response.")
        fallback_msg = (
            "Namaste! KisaanVaani AI Assistant mein aapka swagat hai. 🌾\n\n"
            "Abhi hamara AI Sahayak sandbox/demo mode mein chal raha hai kyunki `OPENROUTER_API_KEY` configured nahi hai.\n\n"
            "Kripya isey activate karne ke liye local `.env` file ya Render Environment Settings mein apni **OpenRouter API Key** darj karein."
        )
        try:
            await save_message(req.farmer_id, req.session_id, "user", req.message)
            await save_message(req.farmer_id, req.session_id, "assistant", fallback_msg)
        except Exception as e:
            logger.warning(f"History save failed: {e}")
            
        return ChatResponse(response=fallback_msg, session_id=req.session_id, tool_used="fallback")

    user = None
    try:
        sb = get_supabase()
        res = sb.table("users").select("*").eq("phone", req.farmer_id).execute()
        user = res.data[0] if res.data else None
    except Exception as db_err:
        logger.warning(f"Supabase connection/fetch failed (falling back to guest defaults): {db_err}")

    district   = user.get("district", "") if user else ""
    state_name = user.get("state", "")    if user else ""
    city       = user.get("city", "")     if user else ""
    name       = user.get("name", "Kisaan") if user else "Kisaan"

    # Use profile data from DB if available, otherwise from request payload
    district   = user.get("district", "") if user else (req.district or "")
    state_name = user.get("state", "")    if user else (req.state or "")
    city       = user.get("city", "")     if user else (req.city or "")
    name       = user.get("name", "Kisaan") if user else (req.name or "Kisaan")

    # Final fallbacks if still empty
    if not district:   district   = city or "Delhi"
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

    # DISABLED MEMORY: Always start with an empty history for a fresh interaction
    history_msgs = []

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

        # SAFETY NET: If AI responded in English but user wants Hindi/Punjabi/etc,
        # translate the answer back to the user's selected language
        if language != "en-IN" and answer:
            # Quick check: if answer is mostly ASCII (English), translate it
            ascii_chars = sum(1 for c in answer if ord(c) < 128)
            total_chars = len(answer)
            if total_chars > 0 and (ascii_chars / total_chars) > 0.8:
                logger.info(f"Response appears English, translating to {language}")
                try:
                    answer = await translate_text(answer, "en-IN", language)
                except Exception as tr_err:
                    logger.warning(f"Translation back failed: {tr_err}")

    except Exception as e:
        logger.exception("Agent error")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    try:
        await save_message(req.farmer_id, req.session_id, "user", req.message)
        await save_message(req.farmer_id, req.session_id, "assistant", answer)
    except Exception as e:
        logger.warning(f"History save failed: {e}")

    return ChatResponse(response=answer, session_id=req.session_id, tool_used=intent)



