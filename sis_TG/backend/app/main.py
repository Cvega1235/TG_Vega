from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
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
from app.auth.dependencies import require_role
from app.migration_tool.importer import import_json, import_csv_data, import_sqlite


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    # Seed superadmin
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(restaurants_router)
app.include_router(dashboard_router)
app.include_router(exports_router)
app.include_router(ml_router)
app.include_router(scraping_router)


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
