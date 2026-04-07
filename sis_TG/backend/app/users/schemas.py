import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr

ALL_PERMISSIONS = ["dashboard", "restaurants", "clients", "ml-analysis", "reports"]


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "viewer"
    permissions: list[str] | None = None  # None = acceso a todas las secciones


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    permissions: list[str] | None = None


class UserUpdateMe(BaseModel):
    full_name: str | None = None
    password: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    permissions: list[str] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
