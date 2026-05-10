import time
import collections
import threading
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Depends, Request, Response, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db, engine, Base
from app.users.models import User
from app.auth.security import hash_password
from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.restaurants.router import router as restaurants_router
from app.dashboard.router import router as dashboard_router
from app.exports.router import router as exports_router
from app.ml.router import router as ml_router
from app.scraping.router import router as scraping_router
from app.security.router import router as security_router
from app.auth.dependencies import require_role
from app.migration_tool.importer import import_json, import_csv_data, import_sqlite


# ── Rate Limiter en memoria ────────────────────────────────────────────────────
# Ventana deslizante: máx. 60 req/min por IP en rutas generales,
# 10 req/min en rutas de autenticación.
_rate_lock = threading.Lock()
_windows: dict[str, collections.deque] = {}

def _is_rate_limited(key: str, max_requests: int, window_seconds: int) -> bool:
    now = time.time()
    with _rate_lock:
        if key not in _windows:
            _windows[key] = collections.deque()
        dq = _windows[key]
        # Eliminar entradas fuera de la ventana
        while dq and dq[0] < now - window_seconds:
            dq.popleft()
        if len(dq) >= max_requests:
            return True
        dq.append(now)
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Obtener IP del cliente
        forwarded = request.headers.get("X-Forwarded-For")
        ip = forwarded.split(",")[0].strip() if forwarded else (
            request.client.host if request.client else "unknown"
        )

        path = request.url.path

        # Rutas de autenticación: límite estricto (10/min)
        if path.startswith("/api/auth/login") or path.startswith("/api/auth/verify"):
            key = f"auth:{ip}"
            if _is_rate_limited(key, max_requests=10, window_seconds=60):
                return Response(
                    content='{"detail":"Demasiadas solicitudes. Espere un momento."}',
                    status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": "60"},
                )

        # Rutas de API general: límite amplio (120/min)
        elif path.startswith("/api/"):
            key = f"api:{ip}"
            if _is_rate_limited(key, max_requests=120, window_seconds=60):
                return Response(
                    content='{"detail":"Demasiadas solicitudes. Espere un momento."}',
                    status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": "60"},
                )

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # Solo activar HSTS en producción (HTTPS)
        # response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == settings.SUPERADMIN_EMAIL).first()
        if not existing:
            admin = User(
                email=settings.SUPERADMIN_EMAIL,
                hashed_password=hash_password(settings.SUPERADMIN_PASSWORD),
                full_name="Super Administrador",
                role="superadmin",
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(
    title="Don Piotr - Sistema de Inteligencia de Mercado",
    description="Dashboard para identificar clientes potenciales de embutidos",
    version="1.0.0",
    lifespan=lifespan,
)

# Middlewares — orden: CORS → RateLimit → SecurityHeaders
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(restaurants_router)
app.include_router(dashboard_router)
app.include_router(exports_router)
app.include_router(ml_router)
app.include_router(scraping_router)
app.include_router(security_router)


# Import endpoints
@app.post("/api/import/json", tags=["import"])
async def import_json_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    content = await file.read()
    return import_json(db, content, user_id=current_user.id)


@app.post("/api/import/csv", tags=["import"])
async def import_csv_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    content = await file.read()
    return import_csv_data(db, content, user_id=current_user.id)


@app.post("/api/import/sqlite", tags=["import"])
async def import_sqlite_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    content = await file.read()
    return import_sqlite(db, content, user_id=current_user.id)


@app.get("/api/health")
def health():
    return {"status": "ok"}
