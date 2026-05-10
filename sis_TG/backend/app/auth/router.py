from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.schemas import (
    LoginRequest, TokenResponse, RefreshRequest, OTPResponse, VerifyOTPRequest,
)
from app.auth.service import AuthService
from app.auth.security import decode_token
from app.auth.dependencies import get_current_user
from app.users.models import User
from app.users.schemas import UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/login", response_model=OTPResponse)
def login(request: LoginRequest, req: Request, db: Session = Depends(get_db)):
    ip = _get_client_ip(req)
    ua = req.headers.get("User-Agent", "")[:300]

    service = AuthService(db)
    user, reason = service.authenticate_user(
        request.email, request.password, ip_address=ip, user_agent=ua
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=reason,
        )
    otp_token = service.generate_and_send_otp(user)
    return OTPResponse(
        otp_token=otp_token,
        email=service.mask_email(user.email),
    )


@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(request: VerifyOTPRequest, req: Request, db: Session = Depends(get_db)):
    ip = _get_client_ip(req)
    ua = req.headers.get("User-Agent", "")[:300]

    payload = decode_token(request.otp_token)
    if payload is None or payload.get("type") != "otp":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token OTP invalido o expirado",
        )

    user_id = payload.get("sub")
    service = AuthService(db)

    if not service.verify_otp(user_id, request.code, ip_address=ip, user_agent=ua):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Codigo incorrecto o expirado",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    return service.create_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    payload = decode_token(request.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalido o expirado",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
        )

    service = AuthService(db)
    return service.create_tokens(user)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
