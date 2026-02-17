from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import require_role
from app.users.models import User
from app.dashboard.schemas import (
    DashboardStats, ChartDataPoint, MapDataPoint, TopScoredItem,
)
from app.dashboard.service import DashboardService
from app.scoring.engine import calculate_all_scores

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_stats()


@router.get("/by-zone", response_model=list[ChartDataPoint])
def get_by_zone(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_by_zone()


@router.get("/by-rating", response_model=list[ChartDataPoint])
def get_by_rating(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_by_rating()


@router.get("/by-cuisine", response_model=list[ChartDataPoint])
def get_by_cuisine(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_by_cuisine()


@router.get("/by-source", response_model=list[ChartDataPoint])
def get_by_source(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_by_source()


@router.get("/by-status", response_model=list[ChartDataPoint])
def get_by_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_by_status()


@router.get("/map-data", response_model=list[MapDataPoint])
def get_map_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_map_data()


@router.get("/top-scores", response_model=list[TopScoredItem])
def get_top_scores(
    limit: int = Query(15, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_top_scores(limit)


@router.post("/recalculate-scores")
def recalculate_scores(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    count = calculate_all_scores(db)
    return {"message": f"Scores recalculados para {count} restaurantes"}
