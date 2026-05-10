from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[uuid.UUID] = None
    user_email: Optional[str] = None
    action: str
    resource: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[str] = None
    status: str
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SecurityStatsResponse(BaseModel):
    total_logs: int
    failed_logins_today: int
    locked_accounts: int
    active_alerts: int


class SecurityAlertResponse(BaseModel):
    type: str          # brute_force | locked_account | suspicious_ip
    severity: str      # high | medium | low
    description: str
    ip_address: Optional[str] = None
    user_email: Optional[str] = None
    count: int
    last_seen: datetime
