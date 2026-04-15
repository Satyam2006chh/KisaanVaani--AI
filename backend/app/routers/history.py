from datetime import datetime

from fastapi import APIRouter

from app.db.mongo import get_db

router = APIRouter(prefix="/api/history", tags=["History"])


async def save_message(farmer_id: str, session_id: str, role: str, content: str):
    db = get_db()
    await db["messages"].insert_one({
        "farmer_id":  farmer_id,
        "session_id": session_id,
        "role":       role,
        "content":    content,
        "timestamp":  datetime.utcnow(),
    })


@router.get("/{farmer_id}")
async def get_history(farmer_id: str, limit: int = 50):
    db = get_db()
    cursor = db["messages"].find({"farmer_id": farmer_id}, {"_id": 0}).sort("timestamp", -1).limit(limit)
    messages = await cursor.to_list(length=limit)
    return {"farmer_id": farmer_id, "messages": list(reversed(messages))}


@router.get("/{farmer_id}/session/{session_id}")
async def get_session(farmer_id: str, session_id: str):
    db = get_db()
    cursor = db["messages"].find({"farmer_id": farmer_id, "session_id": session_id}, {"_id": 0}).sort("timestamp", 1)
    messages = await cursor.to_list(length=200)
    return {"session_id": session_id, "messages": messages}


@router.delete("/{farmer_id}")
async def clear_history(farmer_id: str):
    db = get_db()
    result = await db["messages"].delete_many({"farmer_id": farmer_id})
    return {"deleted_count": result.deleted_count}
