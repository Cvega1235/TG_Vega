"""Modelo de base de datos para el registro de auditoría."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Quién
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Qué
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    # Acciones posibles:
    # LOGIN_SUCCESS, LOGIN_FAILED, LOGIN_LOCKED, OTP_VERIFIED, OTP_FAILED,
    # LOGOUT, RESTAURANT_STATUS_CHANGE, DATA_EXPORTED, ML_RUN, SCRAPING_RUN,
    # USER_CREATED, USER_UPDATED, USER_DELETED, ACCOUNT_UNLOCKED, DATA_ENCRYPTED

    resource: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Resultado
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    # success | failure | warning

    # Contexto de red
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(300), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
