import random
import time
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.core.security import create_access_token

router = APIRouter()

# In-memory store for OTPs and Farmers (resilient, works with or without PostgreSQL)
OTP_STORE: Dict[str, Dict[str, Any]] = {}

# In-memory farmer profile store
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
                "mean_ndvi": 0.62
            }
        ]
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
                "mean_ndvi": 0.54
            }
        ]
    }
}

class OTPRequest(BaseModel):
    phone_number: str = Field(..., description="10-digit Indian mobile number")
    farmer_name: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None

class OTPVerify(BaseModel):
    phone_number: str
    otp: str

@router.post("/request-otp", summary="Request Verification Code (OTP) for Farmer Login/Register")
async def request_otp(payload: OTPRequest):
    """
    Generates a 6-digit verification code for the farmer's mobile number.
    Returns the verification code in response for effortless local testing.
    """
    phone = payload.phone_number.strip().replace("+91", "").replace(" ", "")
    if len(phone) < 10 or not phone.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid 10-digit Indian mobile number."
        )

    code = f"{random.randint(100000, 999999)}"
    OTP_STORE[phone] = {
        "code": code,
        "expires_at": time.time() + 600
    }

    if phone not in FARMER_STORE:
        FARMER_STORE[phone] = {
            "name": payload.farmer_name or f"Farmer {phone[-4:]}",
            "phone_number": phone,
            "state": payload.state or "Punjab",
            "district": payload.district or "Ludhiana",
            "village": "",
            "language": "hi",
            "plots": []
        }
    elif payload.farmer_name:
        FARMER_STORE[phone]["name"] = payload.farmer_name

    return {
        "status": "success",
        "message": f"Verification code sent to +91 {phone}",
        "phone_number": phone,
        "verification_code": code,
        "is_registered": len(FARMER_STORE[phone]["plots"]) > 0
    }

@router.post("/verify-otp", summary="Verify Code and get JWT token with Farmer Profile")
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
            detail="Invalid or expired verification code. Use code '123456' or request a new code."
        )

    if phone in OTP_STORE:
        del OTP_STORE[phone]

    token = create_access_token(subject=phone)
    profile = FARMER_STORE.get(phone, {
        "name": f"Farmer {phone[-4:]}",
        "phone_number": phone,
        "state": "Punjab",
        "district": "Ludhiana",
        "village": "",
        "language": "hi",
        "plots": []
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "phone_number": phone,
        "farmer": profile
    }

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
            "plots": []
        }
    return farmer

@router.get("/farmers-list", summary="List Available Demo Farmer Accounts")
async def list_farmers():
    return [
        {
            "name": v["name"],
            "phone_number": k,
            "state": v["state"],
            "district": v["district"],
            "plots_count": len(v["plots"])
        }
        for k, v in FARMER_STORE.items()
    ]
