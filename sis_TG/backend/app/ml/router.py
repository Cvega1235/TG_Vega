"""Router de endpoints para el módulo de Machine Learning."""

import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.ml.schemas import (
    ClusterProfileResponse,
    MLRunResponse,
    MLRunResultResponse,
    TopProspectResponse,
    ValidationReport,
)
from app.ml.service import MLService
from app.users.models import User

logger = logging.getLogger("app.ml.router")

router = APIRouter(prefix="/api/ml", tags=["ml"])


@router.post("/run", response_model=MLRunResultResponse)
def run_ml_pipeline(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Ejecuta el pipeline completo de ML (solo admin)."""
    try:
        service = MLService(db)
        return service.run_pipeline()
    except Exception as e:
        logger.error(f"Error en pipeline ML: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest-run", response_model=MLRunResponse | None)
def get_latest_run(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    """Obtiene la metadata de la última ejecución ML."""
    service = MLService(db)
    return service.get_latest_run()


@router.get("/clusters", response_model=list[ClusterProfileResponse])
def get_cluster_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    """Obtiene los perfiles descriptivos de cada cluster."""
    service = MLService(db)
    return service.get_cluster_profiles()


@router.get("/top-prospects", response_model=list[TopProspectResponse])
def get_top_prospects(
    limit: int = Query(20, ge=1, le=100),
    include_clients: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    """Obtiene los top prospectos por score compuesto ML."""
    service = MLService(db)
    return service.get_top_prospects(limit=limit, include_clients=include_clients)


@router.get("/recommendations")
def get_recommendations(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role("viewer")),
):
    """Recomendaciones estratégicas para la toma de decisiones comerciales.

    Retorna cuatro secciones accionables:
    - acciones_rapidas: prospectos ya contactados con score alto (más cerca de cerrar)
    - top_sin_contactar: mejores prospectos aún no trabajados
    - zonas_oportunidad: zonas con mayor concentración de prospectos de calidad
    - segmentos_afines: tipos de cocina con mayor tasa de conversión histórica
    """
    service = MLService(db)
    return service.get_recommendations()


@router.get("/validation", response_model=ValidationReport | None)
def get_validation_report(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_role("viewer")),
):
    """Reporte de validación de la última ejecución ML.

    Incluye métricas de calidad del clustering (Silhouette, Davies-Bouldin,
    Calinski-Harabasz) y métricas del clasificador supervisado de conversión
    (Precision, Recall, F1, AUC-ROC con validación cruzada estratificada).
    """
    service = MLService(db)
    return service.get_validation_report()
