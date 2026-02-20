from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class OTPResponse(BaseModel):
    otp_token: str
    email: str
    message: str = "Codigo de verificacion enviado a tu email"


class VerifyOTPRequest(BaseModel):
    otp_token: str
    code: str
