from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import Optional
import jwt
import random
import string
from app.models.schemas import OTPRequest, OTPVerify, Token, UserOut
from app.db.mongo import get_db
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["Auth"])
security = HTTPBearer()

# Simple in-memory OTP store (use Redis in production)
_otp_store: dict[str, tuple[str, datetime]] = {}

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

def _generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))

def _create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Validate JWT token and return current user."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        phone: str = payload.get("sub")
        if phone is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = get_db()
    user = await db["users"].find_one({"phone": phone}, {"_id": 0, "password": 0})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user

@router.post("/otp/send", status_code=status.HTTP_200_OK)
async def send_otp(req: OTPRequest):
    """
    Send OTP to phone number.
    In production: Integrate with Twilio/MSG91.
    For demo: OTP is always '123456' or generated and printed.
    """
    if not req.phone or len(req.phone) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number")

    # For demo: fixed OTP. In production, generate random
    otp = "123456" if settings.app_env == "development" else _generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=10)
    _otp_store[req.phone] = (otp, expiry)

    # TODO: Integrate SMS gateway (Twilio/MSG91)
    print(f"[OTP] Phone: {req.phone}, OTP: {otp}")

    return {
        "message": "OTP sent successfully",
        "phone": req.phone,
        "demo_otp": otp if settings.app_env == "development" else None
    }

@router.post("/otp/verify", response_model=Token)
async def verify_otp_and_login(req: OTPVerify):
    """
    Verify OTP and login/signup user.
    Returns JWT token on success.
    """
    if req.phone not in _otp_store:
        raise HTTPException(status_code=400, detail="OTP not requested or expired")

    stored_otp, expiry = _otp_store[req.phone]

    if datetime.utcnow() > expiry:
        del _otp_store[req.phone]
        raise HTTPException(status_code=400, detail="OTP expired")

    if req.otp != stored_otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # OTP verified - remove from store
    del _otp_store[req.phone]

    db = get_db()
    users_col = db["users"]

    # Check if user exists
    existing_user = await users_col.find_one({"phone": req.phone})

    if existing_user:
        # Existing user - update last login
        await users_col.update_one(
            {"phone": req.phone},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        user_data = existing_user
    else:
        # New user - create profile
        if not req.name:
            raise HTTPException(status_code=400, detail="Name required for new users")

        new_user = {
            "phone": req.phone,
            "name": req.name,
            "language": req.language or "hi-IN",
            "district": req.district or "Delhi",
            "state": req.state or "Delhi",
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow(),
        }
        await users_col.insert_one(new_user)
        user_data = new_user

    # Generate JWT token
    access_token = _create_access_token(data={"sub": req.phone})

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserOut(
            farmer_id=str(user_data.get("phone", req.phone)),
            name=user_data.get("name", req.name),
            language=user_data.get("language", req.language),
            district=user_data.get("district", req.district),
            state=user_data.get("state", req.state),
        )
    )

@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current logged-in user profile."""
    return UserOut(
        farmer_id=str(current_user.get("phone", "")),
        name=current_user.get("name", ""),
        language=current_user.get("language", "hi-IN"),
        district=current_user.get("district", "Delhi"),
        state=current_user.get("state", "Delhi"),
    )

@router.post("/refresh")
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """Refresh JWT token."""
    new_token = _create_access_token(data={"sub": current_user["phone"]})
    return {"access_token": new_token, "token_type": "bearer"}
