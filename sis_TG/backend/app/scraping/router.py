"""Router de endpoints para el módulo de Scraping."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from pydantic import BaseModel

from app.auth.dependencies import require_role
from app.database import get_db
from app.scraping.service import ScrapingService, get_job, list_jobs
from app.users.models import User
from app.restaurants.models import Restaurant, ScrapingImport
from sqlalchemy import func


class EnrichApplyRequest(BaseModel):
    updates: list[dict]  # [{restaurant_id, updates: {field: value}}]

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


@router.get("/history")
def scraping_history(
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role("admin")),
):
    """Retorna el historial de importaciones ordenado por fecha descendente."""
    rows = (
        db.query(ScrapingImport)
        .order_by(ScrapingImport.imported_at.desc())
        .limit(limit)
        .all()
    )

    total_restaurants = db.query(func.count(Restaurant.id)).scalar() or 0

    return {
        "total_restaurants": total_restaurants,
        "runs": [
            {
                "id": r.id,
                "source_file": r.source_file,
                "source_type": r.source_type,
                "records_total": r.records_total,
                "records_imported": r.records_imported,
                "records_skipped": r.records_skipped,
                "imported_at": r.imported_at.isoformat(),
            }
            for r in rows
        ],
    }


# ---------------------------------------------------------------------------
# Enriquecimiento de datos de clientes
# ---------------------------------------------------------------------------

@router.post("/enrich")
def start_enrichment(
    headless: bool = Query(True),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role("analista")),
):
    """Lanza el enriquecimiento en background para todos los clientes con
    datos faltantes. Retorna job_id para hacer polling con GET /enrich/status/{job_id}."""
    service = ScrapingService(db)
    job_id = service.start_enrichment(headless=headless)
    return {"job_id": job_id, "message": "Enriquecimiento iniciado en segundo plano."}


@router.get("/enrich/status/{job_id}")
def enrich_status(
    job_id: str,
    _current_user: User = Depends(require_role("analista")),
):
    """Estado del trabajo de enriquecimiento.

    Cuando status = 'completed', el campo 'results' contiene la lista de
    restaurantes encontrados con los nuevos datos para revisión.
    """
    from app.scraping.service import _ENRICH_JOBS
    job = _ENRICH_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    return {"job_id": job_id, **job}


@router.post("/enrich/apply")
def apply_enrichment(
    data: EnrichApplyRequest,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role("analista")),
):
    """Aplica las actualizaciones de enriquecimiento confirmadas por el usuario.

    Cada entrada en 'updates' debe tener restaurant_id y un dict 'updates'
    con los campos a sobreescribir (solo se aplican si el campo sigue vacío).
    """
    ALLOWED_FIELDS = {"telefono", "latitud", "longitud", "rating", "num_resenas", "tipo_cocina", "website_url"}
    applied = 0

    for entry in data.updates:
        rid = entry.get("restaurant_id")
        field_updates = entry.get("updates", {})
        if not rid or not field_updates:
            continue

        restaurant = db.query(Restaurant).filter(Restaurant.id == rid).first()
        if not restaurant:
            continue

        changed = False
        for field, val in field_updates.items():
            if field not in ALLOWED_FIELDS:
                continue
            if getattr(restaurant, field, None) is None and val is not None:
                setattr(restaurant, field, val)
                changed = True

        if changed:
            applied += 1

    db.commit()
    return {"applied": applied}
