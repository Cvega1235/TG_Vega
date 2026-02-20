from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.users.models import User
from app.auth.models import OTPCode
from app.auth.security import (
    verify_password, create_access_token, create_refresh_token,
    generate_otp_code, create_otp_token,
)
from app.auth.email_service import send_otp_email


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate_user(self, email: str, password: str) -> User | None:
        user = self.db.query(User).filter(User.email == email).first()
        if user is None or not user.is_active:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def create_tokens(self, user: User) -> dict:
        token_data = {"sub": str(user.id), "role": user.role}
        return {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
            "token_type": "bearer",
        }

    def generate_and_send_otp(self, user: User) -> str:
        """Genera OTP, lo guarda en DB, envia email y retorna otp_token."""
        # Invalidar OTPs previos no usados
        self.db.query(OTPCode).filter(
            OTPCode.user_id == user.id,
            OTPCode.is_used == False,  # noqa: E712
        ).delete()

        # Generar nuevo codigo
        code = generate_otp_code()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.OTP_EXPIRE_MINUTES
        )

        otp = OTPCode(
            user_id=user.id,
            code=code,
            expires_at=expires_at,
        )
        self.db.add(otp)
        self.db.commit()

        # Enviar email
        send_otp_email(user.email, code, user.full_name)

        # Retornar token OTP firmado
        return create_otp_token(str(user.id))

    def verify_otp(self, user_id: str, code: str) -> bool:
        """Verifica el codigo OTP para el usuario dado."""
        now = datetime.now(timezone.utc)
        otp = (
            self.db.query(OTPCode)
            .filter(
                OTPCode.user_id == user_id,
                OTPCode.code == code,
                OTPCode.is_used == False,  # noqa: E712
                OTPCode.expires_at > now,
            )
            .first()
        )
        if otp is None:
            return False

        otp.is_used = True
        self.db.commit()
        return True

    @staticmethod
    def mask_email(email: str) -> str:
        """Enmascara email: 'admin@donpiotr.com' -> 'a***n@donpiotr.com'"""
        local, domain = email.split("@")
        if len(local) <= 2:
            masked = local[0] + "***"
        else:
            masked = local[0] + "***" + local[-1]
        return f"{masked}@{domain}"
