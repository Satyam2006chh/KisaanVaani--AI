import random
import string
import logging
from datetime import datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.db.supabase import get_supabase
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

    sb = get_supabase()
    res = sb.table("users").select("*").eq("phone", phone).execute()
    if not res.data:
        raise HTTPException(status_code=401, detail="User not found")
    return res.data[0]


@router.post("/otp/send", status_code=status.HTTP_200_OK)
async def send_otp(req: OTPRequest):
    if not req.phone or len(req.phone) < 10:
        raise HTTPException(status_code=400, detail="Invalid phone number")

    otp = "123456"
    _otp_store[req.phone] = (otp, datetime.utcnow() + timedelta(minutes=10))
    logger.info(f"OTP for {req.phone}: {otp}")

    return {"message": "OTP sent successfully", "phone": req.phone, "demo_otp": otp}


@router.post("/otp/verify", response_model=Token)
async def verify_otp(req: OTPVerify):
    # MASTER DEMO OTP: 123456 always works and survives server restarts
    is_demo = (req.otp == "123456")
    
    if not is_demo:
        if req.phone not in _otp_store:
            logger.warning(f"OTP not found in store for {req.phone}")
            raise HTTPException(status_code=400, detail="OTP not requested or expired")

        stored_otp, expiry = _otp_store[req.phone]
        if datetime.utcnow() > expiry:
            _otp_store.pop(req.phone, None)
            raise HTTPException(status_code=400, detail="OTP expired")
        
        if req.otp != stored_otp:
            raise HTTPException(status_code=400, detail="Invalid OTP")
    else:
        logger.info(f"Demo OTP used for {req.phone}")

    sb = get_supabase()
    res = sb.table("users").select("*").eq("phone", req.phone).execute()

    if res.data:
        user_data = res.data[0]
        sb.table("users").update({"last_login": datetime.utcnow().isoformat()}).eq("phone", req.phone).execute()
    else:
        if not req.name:
            # We don't pop the OTP here so they can retry with their name
            raise HTTPException(status_code=400, detail="Name required for new users")
        
        # 1. Fetch available columns dynamically to avoid crashes if schema is missing 'district' or 'state'
        try:
            sample = sb.table("users").select("*").limit(1).execute()
            if sample.data:
                available_cols = set(sample.data[0].keys())
            else:
                available_cols = {"phone", "name", "language", "created_at"}
        except Exception:
            available_cols = {"phone", "name", "language", "created_at"}

        # 2. Build safe insert dictionary
        new_user = {
            "phone": req.phone,
            "name": req.name,
            "language": req.language or "hi-IN",
            "created_at": datetime.utcnow().isoformat(),
            "last_login": datetime.utcnow().isoformat(),
        }
        if "district" in available_cols: new_user["district"] = req.district or ""
        if "state" in available_cols:    new_user["state"] = req.state or ""
        if "city" in available_cols:     new_user["city"] = req.city or ""
        
        try:
            insert_res = sb.table("users").insert(new_user).execute()
            if not insert_res.data:
                 raise Exception("Failed to create user record")
            user_data = insert_res.data[0]
        except Exception as e:
            logger.error(f"DATABASE ERROR: {e}")
            raise HTTPException(status_code=500, detail=f"Error creating your profile: {str(e)}")

    response = Token(
        access_token=_make_token(req.phone),
        token_type="bearer",
        user=UserOut(
            farmer_id=user_data["phone"],
            name=user_data.get("name", ""),
            language=user_data.get("language", "hi-IN"),
            district=user_data.get("district", ""),
            state=user_data.get("state", ""),
            city=user_data.get("city", "") if "city" in user_data else "",
        ),
    )
    
    # Success! Now clear the OTP
    _otp_store.pop(req.phone, None)
    return response


@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserOut(
        farmer_id=current_user["phone"],
        name=current_user.get("name", ""),
        language=current_user.get("language", "hi-IN"),
        district=current_user.get("district", ""),
        state=current_user.get("state", ""),
        city=current_user.get("city", "") if "city" in current_user else "",
    )


@router.post("/refresh")
async def refresh_token(current_user: dict = Depends(get_current_user)):
    return {"access_token": _make_token(current_user["phone"]), "token_type": "bearer"}


@router.post("/profile/update")
async def update_profile(data: dict):
    phone = data.get("phone")
    if not phone:
        raise HTTPException(status_code=400, detail="Phone required")
    
    sb = get_supabase()
    # 1. Fetch available columns dynamically to avoid crashes if schema is missing 'city' or 'lat'
    try:
        sample = sb.table("users").select("*").limit(1).execute()
        if sample.data:
            available_cols = set(sample.data[0].keys())
        else:
            available_cols = {"phone", "name", "district", "state"}
    except Exception:
        available_cols = {"phone", "name", "district", "state"}

    # 2. Build safe update dictionary
    update_data = {}
    lat = data.get("lat", data.get("latitude"))
    lon = data.get("lon", data.get("longitude"))

    if "district" in available_cols and data.get("district"): update_data["district"] = data.get("district")
    if "state" in available_cols and data.get("state"):       update_data["state"] = data.get("state")
    if "city" in available_cols and data.get("city"):         update_data["city"] = data.get("city")
    if "lat" in available_cols and lat is not None:           update_data["lat"] = lat
    if "lon" in available_cols and lon is not None:           update_data["lon"] = lon

    if not update_data:
        return {"status": "skipped", "message": "No valid columns to update"}

    res = sb.table("users").update(update_data).eq("phone", phone).execute()
    return {"status": "success", "data": res.data}
