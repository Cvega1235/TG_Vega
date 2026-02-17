"""Router de endpoints para el módulo de Scraping."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.scraping.service import ScrapingService
from app.users.models import User

router = APIRouter(prefix="/api/scraping", tags=["scraping"])


@router.post("/run")
def run_scraper(
    source: str = Query("all", regex="^(bolivia|gmaps|all)$"),
    headless: bool = Query(True),
    limit: int | None = Query(None, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Ejecuta el scraper y guarda resultados en la DB (solo admin)."""
    service = ScrapingService(db)
    return service.run_scraper(source=source, headless=headless, limit=limit)
