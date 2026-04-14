from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ─── Auth ────────────────────────────────────────────────────
class UserCreate(BaseModel):
    phone: str
    name: str
    language: str   # e.g. "hi-IN"
    district: str
    state: str

class UserOut(BaseModel):
    farmer_id: str
    name: str
    language: str
    district: str
    state: str

# ─── Chat / History ───────────────────────────────────────────
class ChatMessage(BaseModel):
    role: str          # "user" or "assistant"
    content: str
    timestamp: datetime = datetime.utcnow()
    audio_available: bool = False

class ChatRequest(BaseModel):
    farmer_id: str
    session_id: str
    message: str
    language: str = "hi-IN"

class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_used: Optional[str] = None

# ─── Voice ─────────────────────────────────────────────────────
class TTSRequest(BaseModel):
    text: str
    language: str = "hi-IN"
