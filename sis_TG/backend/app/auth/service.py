from datetime import datetime, timedelta, timezone
from typing import Optional

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

    def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> tuple[Optional[User], str]:
        """
        Verifica credenciales con control de bloqueo por intentos fallidos.

        Returns:
            (user, reason) donde reason es "" en éxito o un mensaje de error.
        """
        from app.security.service import AuditService
        audit = AuditService(self.db)

        user = self.db.query(User).filter(User.email == email).first()

        # Usuario inexistente — no revelar si existe
        if user is None:
            audit.log(
                "LOGIN_FAILED",
                user_email=email,
                status="failure",
                ip_address=ip_address,
                user_agent=user_agent,
                details="Usuario no encontrado",
            )
            return None, "Email o contrasena incorrectos"

        # Cuenta inactiva
        if not user.is_active:
            audit.log(
                "LOGIN_FAILED",
                user_id=user.id,
                user_email=email,
                status="failure",
                ip_address=ip_address,
                user_agent=user_agent,
                details="Cuenta inactiva",
            )
            return None, "Cuenta inactiva"

        # Cuenta bloqueada
        now = datetime.now(timezone.utc)
        if user.locked_until and user.locked_until > now:
            remaining = int((user.locked_until - now).total_seconds() / 60) + 1
            audit.log(
                "LOGIN_LOCKED",
                user_id=user.id,
                user_email=email,
                status="failure",
                ip_address=ip_address,
                user_agent=user_agent,
                details=f"Cuenta bloqueada — {remaining} min restantes",
            )
            return None, f"Cuenta bloqueada. Intente en {remaining} minuto(s)."

        # Contraseña incorrecta
        if not verify_password(password, user.hashed_password):
            user.failed_attempts = (user.failed_attempts or 0) + 1

            if user.failed_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=settings.LOCKOUT_MINUTES)
                self.db.commit()
                audit.log(
                    "LOGIN_LOCKED",
                    user_id=user.id,
                    user_email=email,
                    status="failure",
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details=f"Cuenta bloqueada tras {user.failed_attempts} intentos fallidos",
                )
                return None, (
                    f"Cuenta bloqueada por {settings.LOCKOUT_MINUTES} minutos "
                    f"tras {settings.MAX_LOGIN_ATTEMPTS} intentos fallidos."
                )

            self.db.commit()
            remaining_attempts = settings.MAX_LOGIN_ATTEMPTS - user.failed_attempts
            audit.log(
                "LOGIN_FAILED",
                user_id=user.id,
                user_email=email,
                status="failure",
                ip_address=ip_address,
                user_agent=user_agent,
                details=f"Contraseña incorrecta (intento {user.failed_attempts}/{settings.MAX_LOGIN_ATTEMPTS})",
            )
            return None, f"Email o contrasena incorrectos ({remaining_attempts} intentos restantes)"

        # Éxito — resetear contador
        user.failed_attempts = 0
        user.locked_until = None
        user.last_login_at = now
        self.db.commit()

        audit.log(
            "LOGIN_SUCCESS",
            user_id=user.id,
            user_email=email,
            status="success",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return user, ""

    def create_tokens(self, user: User) -> dict:
        token_data = {"sub": str(user.id), "role": user.role}
        return {
            "access_token": create_access_token(token_data),
            "refresh_token": create_refresh_token(token_data),
            "token_type": "bearer",
        }

    def generate_and_send_otp(self, user: User) -> str:
        """Genera OTP, lo guarda en DB, envía email y retorna otp_token."""
        self.db.query(OTPCode).filter(
            OTPCode.user_id == user.id,
            OTPCode.is_used == False,  # noqa: E712
        ).delete()

        code = generate_otp_code()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.OTP_EXPIRE_MINUTES
        )

        otp = OTPCode(user_id=user.id, code=code, expires_at=expires_at)
        self.db.add(otp)
        self.db.commit()

        send_otp_email(user.email, code, user.full_name)
        return create_otp_token(str(user.id))

    def verify_otp(
        self,
        user_id: str,
        code: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        from app.security.service import AuditService
        audit = AuditService(self.db)

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

        user = self.db.query(User).filter(User.id == user_id).first()

        if otp is None:
            audit.log(
                "OTP_FAILED",
                user_id=user.id if user else None,
                user_email=user.email if user else None,
                status="failure",
                ip_address=ip_address,
                user_agent=user_agent,
                details="Código OTP incorrecto o expirado",
            )
            return False

        otp.is_used = True
        self.db.commit()

        audit.log(
            "OTP_VERIFIED",
            user_id=user.id if user else None,
            user_email=user.email if user else None,
            status="success",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        return True

    @staticmethod
    def mask_email(email: str) -> str:
        local, domain = email.split("@")
        if len(local) <= 2:
            masked = local[0] + "***"
        else:
            masked = local[0] + "***" + local[-1]
        return f"{masked}@{domain}"
