"""Router de endpoints para el módulo de Scraping."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.scraping.service import ScrapingService, get_job, list_jobs
from app.users.models import User

router = APIRouter(prefix="/api/scraping", tags=["scraping"])


@router.post("/run")
def run_scraper(
    source: str = Query("all", regex="^(bolivia|gmaps|all)$"),
    headless: bool = Query(True),
    limit: int | None = Query(None, ge=1, le=500),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    """Lanza el scraper en background y retorna un job_id para hacer polling.

    El scraping se ejecuta en un hilo separado. Usa GET /status/{job_id}
    para consultar el progreso.
    """
    service = ScrapingService(db)
    job_id = service.start_scraper(source=source, headless=headless, limit=limit)
    return {"job_id": job_id, "message": "Scraping iniciado en segundo plano."}


@router.get("/status/{job_id}")
def scraping_status(
    job_id: str,
    _current_user: User = Depends(require_role("admin")),
):
    """Retorna el estado actual de un trabajo de scraping.

    Campos de respuesta:
    - status: "running" | "completed" | "error"
    - steps_done / steps_total: para calcular porcentaje de progreso
    - current_step: descripción de la zona/página que se está procesando ahora
    - imported / skipped: disponibles cuando status = "completed"
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return {"job_id": job_id, **job}


@router.get("/jobs")
def list_scraping_jobs(
    _current_user: User = Depends(require_role("admin")),
):
    """Lista todos los trabajos de scraping registrados en esta sesión del servidor."""
    return list_jobs()
