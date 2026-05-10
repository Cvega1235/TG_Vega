"""Servicio de auditoría y detección de actividad sospechosa."""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.security.models import AuditLog
from app.security.schemas import SecurityAlertResponse, SecurityStatsResponse


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ── Escritura ─────────────────────────────────────────────────────────────

    def log(
        self,
        action: str,
        *,
        user_id: Optional[uuid.UUID] = None,
        user_email: Optional[str] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[str] = None,
        status: str = "success",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        entry = AuditLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource=resource,
            resource_id=str(resource_id) if resource_id is not None else None,
            details=details,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(entry)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()

    # ── Lectura ───────────────────────────────────────────────────────────────

    def get_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        action: Optional[str] = None,
        status: Optional[str] = None,
        user_email: Optional[str] = None,
    ) -> list[AuditLog]:
        q = self.db.query(AuditLog)
        if action:
            q = q.filter(AuditLog.action == action)
        if status:
            q = q.filter(AuditLog.status == status)
        if user_email:
            q = q.filter(AuditLog.user_email.ilike(f"%{user_email}%"))
        return (
            q.order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_stats(self) -> SecurityStatsResponse:
        from app.users.models import User

        total = self.db.query(func.count(AuditLog.id)).scalar() or 0

        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        failed_today = (
            self.db.query(func.count(AuditLog.id))
            .filter(
                AuditLog.action == "LOGIN_FAILED",
                AuditLog.created_at >= today_start,
            )
            .scalar()
            or 0
        )

        locked = (
            self.db.query(func.count(User.id))
            .filter(
                User.locked_until.isnot(None),
                User.locked_until > datetime.now(timezone.utc),
            )
            .scalar()
            or 0
        )

        alerts = len(self.get_alerts())

        return SecurityStatsResponse(
            total_logs=total,
            failed_logins_today=failed_today,
            locked_accounts=locked,
            active_alerts=alerts,
        )

    def get_alerts(self) -> list[SecurityAlertResponse]:
        """
        Detecta actividad sospechosa:
        - IPs con ≥ 3 intentos fallidos en la última hora (fuerza bruta)
        - Cuentas bloqueadas actualmente
        """
        alerts: list[SecurityAlertResponse] = []
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

        # ── Brute force por IP ────────────────────────────────────────────────
        rows = (
            self.db.query(
                AuditLog.ip_address,
                func.count(AuditLog.id).label("cnt"),
                func.max(AuditLog.created_at).label("last"),
            )
            .filter(
                AuditLog.action == "LOGIN_FAILED",
                AuditLog.created_at >= one_hour_ago,
                AuditLog.ip_address.isnot(None),
            )
            .group_by(AuditLog.ip_address)
            .having(func.count(AuditLog.id) >= 3)
            .all()
        )
        for ip, cnt, last in rows:
            alerts.append(
                SecurityAlertResponse(
                    type="brute_force",
                    severity="high" if cnt >= 5 else "medium",
                    description=f"Múltiples intentos de login fallidos desde {ip}",
                    ip_address=ip,
                    count=cnt,
                    last_seen=last,
                )
            )

        # ── Cuentas bloqueadas ────────────────────────────────────────────────
        from app.users.models import User

        locked_users = (
            self.db.query(User)
            .filter(
                User.locked_until.isnot(None),
                User.locked_until > datetime.now(timezone.utc),
            )
            .all()
        )
        for u in locked_users:
            alerts.append(
                SecurityAlertResponse(
                    type="locked_account",
                    severity="medium",
                    description=f"Cuenta bloqueada por intentos excesivos",
                    user_email=u.email,
                    count=u.failed_attempts,
                    last_seen=u.locked_until,
                )
            )

        return alerts
