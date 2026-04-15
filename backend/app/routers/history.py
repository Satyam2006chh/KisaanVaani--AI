from datetime import datetime
from fastapi import APIRouter
from app.db.supabase import get_supabase

router = APIRouter(prefix="/api/history", tags=["History"])


async def save_message(farmer_id: str, session_id: str, role: str, content: str):
    sb = get_supabase()
    sb.table("messages").insert({
        "farmer_id":  farmer_id,
        "session_id": session_id,
        "role":       role,
        "content":    content,
        "timestamp":  datetime.utcnow().isoformat(),
    }).execute()


@router.get("/{farmer_id}")
async def get_history(farmer_id: str, limit: int = 50):
    sb = get_supabase()
    res = sb.table("messages").select("*").eq("farmer_id", farmer_id)\
        .order("timestamp", desc=True).limit(limit).execute()
    messages = list(reversed(res.data or []))
    return {"farmer_id": farmer_id, "messages": messages}


@router.get("/{farmer_id}/session/{session_id}")
async def get_session(farmer_id: str, session_id: str):
    sb = get_supabase()
    res = sb.table("messages").select("*")\
        .eq("farmer_id", farmer_id).eq("session_id", session_id)\
        .order("timestamp").execute()
    return {"session_id": session_id, "messages": res.data or []}


@router.delete("/{farmer_id}")
async def clear_history(farmer_id: str):
    sb = get_supabase()
    res = sb.table("messages").delete().eq("farmer_id", farmer_id).execute()
    return {"deleted_count": len(res.data or [])}
