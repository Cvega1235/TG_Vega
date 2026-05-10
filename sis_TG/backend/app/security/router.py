"""Endpoints de seguridad: auditoría, alertas y gestión de bloqueos."""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import require_role, get_current_user
from app.users.models import User
from app.security.models import AuditLog
from app.security.schemas import (
    AuditLogResponse, SecurityStatsResponse, SecurityAlertResponse,
)
from app.security.service import AuditService
from app.security.encryption import encrypt_field, _get_cipher

router = APIRouter(prefix="/api/security", tags=["security"])


@router.get("/stats", response_model=SecurityStatsResponse)
def get_security_stats(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    return AuditService(db).get_stats()


@router.get("/logs", response_model=list[AuditLogResponse])
def get_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    user_email: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    return AuditService(db).get_logs(
        limit=limit, offset=offset, action=action,
        status=status, user_email=user_email,
    )


@router.get("/alerts", response_model=list[SecurityAlertResponse])
def get_security_alerts(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    return AuditService(db).get_alerts()


@router.post("/users/{user_id}/unlock")
def unlock_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.failed_attempts = 0
    user.locked_until = None
    db.commit()

    AuditService(db).log(
        "ACCOUNT_UNLOCKED",
        user_id=current_user.id,
        user_email=current_user.email,
        resource="user",
        resource_id=str(user_id),
        details=f"Cuenta de {user.email} desbloqueada por {current_user.email}",
    )
    return {"message": f"Cuenta de {user.email} desbloqueada"}


@router.post("/encrypt-existing")
def encrypt_existing_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Cifra los campos telefono y direccion de los restaurantes que aún
    están en texto plano. Operación idempotente: los ya cifrados se omiten.
    """
    if _get_cipher() is None:
        raise HTTPException(
            status_code=400,
            detail="ENCRYPTION_KEY no configurada. Añádala al archivo .env primero.",
        )

    from app.restaurants.models import Restaurant
    from app.security.encryption import decrypt_field

    restaurants = db.query(Restaurant).all()
    updated = 0
    for r in restaurants:
        changed = False
        # Si decrypt == original, está en texto plano → cifrar
        if r.telefono and decrypt_field(r.telefono) == r.telefono:
            r.telefono = encrypt_field(r.telefono)
            changed = True
        if r.direccion and decrypt_field(r.direccion) == r.direccion:
            r.direccion = encrypt_field(r.direccion)
            changed = True
        if changed:
            updated += 1

    db.commit()

    AuditService(db).log(
        "DATA_ENCRYPTED",
        user_id=current_user.id,
        user_email=current_user.email,
        resource="restaurant",
        details=f"{updated} registros cifrados de {len(restaurants)} totales",
    )
    return {"message": f"{updated} registros cifrados correctamente"}


@router.get("/encryption-status")
def encryption_status(
    _current_user: User = Depends(require_role("admin")),
):
    active = _get_cipher() is not None
    return {
        "encryption_active": active,
        "message": (
            "Cifrado AES-128 (Fernet) activo" if active
            else "Cifrado inactivo — configure ENCRYPTION_KEY en .env"
        ),
    }
