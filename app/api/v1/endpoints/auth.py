from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.core.security import create_access_token

router = APIRouter()

class OTPRequest(BaseModel):
    phone_number: str

class OTPVerify(BaseModel):
    phone_number: str
    otp: str

@router.post("/request-otp", summary="Request OTP for Farmer Mobile Login")
async def request_otp(payload: OTPRequest):
    """
    Sends 6-digit OTP via SMS (Simulated as '123456' for dev/testing).
    """
    phone = payload.phone_number.strip()
    if len(phone) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Indian phone number."
        )
    return {
        "message": "OTP sent successfully.",
        "phone_number": phone,
        "dev_otp": "123456"  # Simulated OTP for development
    }

@router.post("/verify-otp", summary="Verify OTP and receive JWT access token")
async def verify_otp(payload: OTPVerify):
    if payload.otp != "123456":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP."
        )
    token = create_access_token(subject=payload.phone_number)
    return {
        "access_token": token,
        "token_type": "bearer",
        "phone_number": payload.phone_number
    }
