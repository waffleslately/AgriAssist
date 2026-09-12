import random
import re
import time
from collections import defaultdict
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.security import create_access_token

router = APIRouter()

# ---------------------------------------------------------------------------
# In-memory stores (MVP — replaced by DB in production)
# ---------------------------------------------------------------------------

OTP_STORE: Dict[str, Dict[str, Any]] = {}

FARMER_STORE: Dict[str, Dict[str, Any]] = {
    "9876543210": {
        "name": "Harpreet Singh",
        "phone_number": "9876543210",
        "state": "Punjab",
        "district": "Ludhiana",
        "village": "Gill",
        "language": "hi",
        "plots": [
            {
                "plot_name": "Khet No. 1 (North)",
                "crop_name": "wheat",
                "area_acres": 3.8,
                "sowing_date": "2025-11-15",
                "stage": "Crown Root Initiation",
                "mean_ndvi": 0.62,
            }
        ],
    },
    "9123456780": {
        "name": "Ramesh Patil",
        "phone_number": "9123456780",
        "state": "Maharashtra",
        "district": "Yavatmal",
        "village": "Bori",
        "language": "mr",
        "plots": [
            {
                "plot_name": "Black Soil Farm",
                "crop_name": "cotton",
                "area_acres": 4.5,
                "sowing_date": "2025-06-25",
                "stage": "Boll Formation",
                "mean_ndvi": 0.54,
            }
        ],
    },
}

# ---------------------------------------------------------------------------
# Rate-limiter: 5 requests / 60 s / IP (sliding window, in-memory)
# ---------------------------------------------------------------------------

_rate_buckets: Dict[str, list] = defaultdict(list)
_RATE_LIMIT = 5
_RATE_WINDOW = 60  # seconds


def _check_rate_limit(ip: str) -> None:
    now = time.time()
    bucket = _rate_buckets[ip]
    # Drop timestamps older than the window
    _rate_buckets[ip] = [t for t in bucket if now - t < _RATE_WINDOW]
    if len(_rate_buckets[ip]) >= _RATE_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait 60 seconds and try again.",
            headers={"Retry-After": "60"},
        )
    _rate_buckets[ip].append(now)


# E.164 for Indian numbers: +91 followed by 6-9 and 9 more digits
_E164_IN = re.compile(r"^\+91[6-9]\d{9}$")


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class OTPRequest(BaseModel):
    phone_number: str = Field(..., description="10-digit Indian mobile number")
    farmer_name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None


class OTPVerify(BaseModel):
    phone_number: str
    otp: str


class FirebaseVerifyRequest(BaseModel):
    id_token: str = Field(..., min_length=10, description="Firebase ID token from client SDK")


# ---------------------------------------------------------------------------
# Legacy mock-OTP endpoints (kept for backward-compat, marked deprecated)
# ---------------------------------------------------------------------------


@router.post(
    "/request-otp",
    summary="[DEPRECATED] Request mock OTP — use /verify-phone (Firebase) instead",
    deprecated=True,
)
async def request_otp(payload: OTPRequest):
    phone = payload.phone_number.strip().replace("+91", "").replace(" ", "")
    if len(phone) < 10 or not phone.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid 10-digit Indian mobile number.",
        )

    code = f"{random.randint(100000, 999999)}"
    OTP_STORE[phone] = {"code": code, "expires_at": time.time() + 600}

    if phone not in FARMER_STORE:
        FARMER_STORE[phone] = {
            "name": payload.farmer_name or f"Farmer {phone[-4:]}",
            "phone_number": phone,
            "state": payload.state or "Punjab",
            "district": payload.district or "Ludhiana",
            "village": "",
            "language": "hi",
            "plots": [],
        }
    elif payload.farmer_name:
        FARMER_STORE[phone]["name"] = payload.farmer_name

    return {
        "status": "success",
        "message": f"Verification code sent to +91 {phone}",
        "phone_number": phone,
        "verification_code": code,
        "is_registered": len(FARMER_STORE[phone]["plots"]) > 0,
    }


@router.post(
    "/verify-otp",
    summary="[DEPRECATED] Verify mock OTP — use /verify-phone (Firebase) instead",
    deprecated=True,
)
async def verify_otp(payload: OTPVerify):
    phone = payload.phone_number.strip().replace("+91", "").replace(" ", "")
    stored = OTP_STORE.get(phone)

    is_valid = False
    if payload.otp == "123456":
        is_valid = True
    elif stored and stored.get("code") == payload.otp and time.time() <= stored.get("expires_at", 0):
        is_valid = True

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired verification code.",
        )

    if phone in OTP_STORE:
        del OTP_STORE[phone]

    token = create_access_token(subject=phone)
    profile = FARMER_STORE.get(
        phone,
        {"name": f"Farmer {phone[-4:]}", "phone_number": phone, "state": "Punjab",
         "district": "Ludhiana", "village": "", "language": "hi", "plots": []},
    )
    return {"access_token": token, "token_type": "bearer", "phone_number": phone, "farmer": profile}


# ---------------------------------------------------------------------------
# NEW: Firebase Phone Auth endpoint
# ---------------------------------------------------------------------------


@router.post(
    "/verify-phone",
    summary="Verify Firebase Phone ID token and issue app session JWT",
)
async def verify_phone(payload: FirebaseVerifyRequest, request: Request):
    """
    Accepts a Firebase ID token obtained after the client completes
    Phone OTP verification via the Firebase JS/iOS/Android SDK.

    Steps:
    1. Rate-limit per IP (5 req / 60 s).
    2. Verify the token server-side with Firebase Admin SDK.
    3. Validate the phone number is Indian E.164.
    4. Upsert the farmer record.
    5. Issue and return the app's own JWT.

    Never logs the raw id_token or OTP value.
    """
    # 1. Rate-limit
    client_ip = (request.headers.get("X-Forwarded-For") or request.client.host or "unknown").split(",")[0].strip()
    _check_rate_limit(client_ip)

    # 2. Verify Firebase token server-side
    try:
        from app.services.firebase_admin_service import verify_firebase_id_token
        decoded = verify_firebase_id_token(payload.id_token)
    except ValueError as exc:
        # Firebase not configured — server misconfiguration
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Firebase authentication is not configured on this server: {exc}",
        )
    except Exception as exc:
        # Invalid / expired / revoked token
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token verification failed. Please sign in again.",
        )

    # 3. Extract & validate phone number (E.164 +91XXXXXXXXXX)
    firebase_uid: str = decoded.get("uid", "")
    raw_phone: str = decoded.get("phone_number", "")

    if not raw_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token does not contain a phone number. Only Phone sign-in is supported.",
        )

    if not _E164_IN.match(raw_phone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Phone number {raw_phone!r} is not a valid Indian mobile number (+91XXXXXXXXXX). "
                "Only Indian numbers are supported."
            ),
        )

    # 4. Normalise to 10-digit key used in FARMER_STORE
    phone10 = raw_phone[3:]  # strip "+91"

    # Upsert farmer record
    if phone10 not in FARMER_STORE:
        FARMER_STORE[phone10] = {
            "name": f"Farmer {phone10[-4:]}",
            "phone_number": phone10,
            "firebase_uid": firebase_uid,
            "state": "Punjab",
            "district": "Ludhiana",
            "village": "",
            "language": "hi",
            "plots": [],
        }
    else:
        # Persist Firebase UID if not already stored
        FARMER_STORE[phone10].setdefault("firebase_uid", firebase_uid)

    profile = FARMER_STORE[phone10]

    # 5. Issue app JWT — subject is the 10-digit phone (consistent with legacy endpoints)
    token = create_access_token(subject=phone10)

    return {
        "access_token": token,
        "token_type": "bearer",
        "phone_number": phone10,
        "is_new_farmer": len(profile.get("plots", [])) == 0,
        "farmer": profile,
    }


# ---------------------------------------------------------------------------
# Firebase frontend config endpoint (serves config from env, never from files)
# ---------------------------------------------------------------------------


@router.get(
    "/firebase-config",
    summary="Get Firebase frontend config (served from server env vars)",
)
async def firebase_config():
    """
    Returns the Firebase Web SDK configuration object.
    Serving from the backend means the values come from env vars and are
    never embedded in static files committed to git.
    """
    if not settings.FIREBASE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase is not configured on this server. Set FIREBASE_API_KEY in .env.",
        )
    return {
        "apiKey": settings.FIREBASE_API_KEY,
        "authDomain": settings.FIREBASE_AUTH_DOMAIN,
        "projectId": settings.FIREBASE_PROJECT_ID,
        "appId": settings.FIREBASE_APP_ID,
        "messagingSenderId": settings.FIREBASE_MESSAGING_SENDER_ID,
    }


# ---------------------------------------------------------------------------
# Existing helper endpoints (unchanged)
# ---------------------------------------------------------------------------


@router.get("/me", summary="Get Current Logged-in Farmer Profile & Plots")
async def get_current_farmer(phone: Optional[str] = None):
    if not phone:
        phone = "9876543210"
    clean_phone = phone.strip().replace("+91", "").replace(" ", "")
    farmer = FARMER_STORE.get(clean_phone)
    if not farmer:
        return {
            "name": f"Farmer {clean_phone[-4:]}",
            "phone_number": clean_phone,
            "state": "Punjab",
            "district": "Ludhiana",
            "plots": [],
        }
    return farmer


@router.get("/farmers-list", summary="List Available Farmer Accounts")
async def list_farmers():
    return [
        {
            "name": v["name"],
            "phone_number": k,
            "state": v["state"],
            "district": v["district"],
            "plots_count": len(v["plots"]),
        }
        for k, v in FARMER_STORE.items()
    ]
