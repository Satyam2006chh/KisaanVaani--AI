from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class OTPRequest(BaseModel):
    phone: str


class OTPVerify(BaseModel):
    phone: str
    otp: str
    name: str = ""
    language: str = "hi-IN"
    district: str = ""
    state: str = ""
    city: str = ""


class UserOut(BaseModel):
    farmer_id: str
    name: str
    language: str
    district: str
    state: str
    city: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ChatRequest(BaseModel):
    farmer_id: str
    session_id: str
    message: str
    english_message: Optional[str] = None
    language: str = "hi-IN"
    image: Optional[str] = None  # Base64 string
    location: Optional[dict] = None # {lat, lon, city}


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_used: Optional[str] = None


class TTSRequest(BaseModel):
    text: str
    language: str = "hi-IN"
    speaker: Optional[str] = None
