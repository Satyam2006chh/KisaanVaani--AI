import random
import string
import logging
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.db.mongo import get_db
from app.models.schemas import OTPRequest, OTPVerify, Token, UserOut

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Auth"])
security = HTTPBearer()

_otp_store: dict[str, tuple[str, datetime]] = {}

ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 30


def _make_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


def _make_token(phone: str) -> str:
    expire = datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS)
    return jwt.encode({"sub": phone, "exp": expire}, settings.secret_key, algorithm=ALGORITHM)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[ALGORITHM])
        phone: str = payload.get("sub")
        if not phone:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = get_db()
    user = await db["users"].find_one({"phone": phone}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/otp/send", status_code=status.HTTP_200_OK)
async def send_otp(req: OTPRequest):
    if not req.phone or len(req.phone) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number")

    otp = "123456" if settings.app_env != "production" else _make_otp()
    _otp_store[req.phone] = (otp, datetime.utcnow() + timedelta(minutes=10))
    logger.info(f"OTP for {req.phone}: {otp}")

    return {
        "message": "OTP sent successfully",
        "phone": req.phone,
        "demo_otp": otp if settings.app_env != "production" else None,
    }


@router.post("/otp/verify", response_model=Token)
async def verify_otp(req: OTPVerify):
    if req.phone not in _otp_store:
        raise HTTPException(status_code=400, detail="OTP not requested or expired")

    stored_otp, expiry = _otp_store[req.phone]

    if datetime.utcnow() > expiry:
        _otp_store.pop(req.phone, None)
        raise HTTPException(status_code=400, detail="OTP expired")

    if req.otp != stored_otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    _otp_store.pop(req.phone, None)

    db = get_db()
    existing = await db["users"].find_one({"phone": req.phone})

    if existing:
        await db["users"].update_one({"phone": req.phone}, {"$set": {"last_login": datetime.utcnow()}})
        user_data = existing
    else:
        if not req.name:
            raise HTTPException(status_code=400, detail="Name required for new users")
        user_data = {
            "phone": req.phone,
            "name": req.name,
            "language": req.language or "hi-IN",
            "district": req.district or "",
            "state": req.state or "",
            "city": req.city or "",
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow(),
        }
        await db["users"].insert_one(user_data)

    return Token(
        access_token=_make_token(req.phone),
        token_type="bearer",
        user=UserOut(
            farmer_id=user_data["phone"],
            name=user_data.get("name", ""),
            language=user_data.get("language", "hi-IN"),
            district=user_data.get("district", ""),
            state=user_data.get("state", ""),
            city=user_data.get("city", ""),
        ),
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserOut(
        farmer_id=current_user["phone"],
        name=current_user.get("name", ""),
        language=current_user.get("language", "hi-IN"),
        district=current_user.get("district", ""),
        state=current_user.get("state", ""),
        city=current_user.get("city", ""),
    )


@router.post("/refresh")
async def refresh_token(current_user: dict = Depends(get_current_user)):
    return {"access_token": _make_token(current_user["phone"]), "token_type": "bearer"}
