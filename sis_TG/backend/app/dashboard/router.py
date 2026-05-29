from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import require_role
from app.users.models import User
from app.dashboard.schemas import (
    DashboardStats, ChartDataPoint, MapDataPoint, TopScoredItem, TopProspectItem,
    ClientHistoryData, RecentSummary,
)
from app.dashboard.service import DashboardService
from app.scoring.engine import calculate_all_scores

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_stats(
    fuente: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_stats(fuente)


@router.get("/by-zone", response_model=list[ChartDataPoint])
def get_by_zone(
    fuente: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_by_zone(fuente)


@router.get("/by-rating", response_model=list[ChartDataPoint])
def get_by_rating(
    fuente: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_by_rating(fuente)


@router.get("/by-cuisine", response_model=list[ChartDataPoint])
def get_by_cuisine(
    fuente: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_by_cuisine(fuente)


@router.get("/by-source", response_model=list[ChartDataPoint])
def get_by_source(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_by_source()


@router.get("/by-status", response_model=list[ChartDataPoint])
def get_by_status(
    fuente: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_by_status(fuente)


@router.get("/map-data", response_model=list[MapDataPoint])
def get_map_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_map_data()


@router.get("/top-prospects", response_model=list[TopProspectItem])
def get_top_prospects(
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_top_prospects(limit)


@router.get("/top-scores", response_model=list[TopScoredItem])
def get_top_scores(
    limit: int = Query(15, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_top_scores(limit)


@router.get("/client-history", response_model=ClientHistoryData)
def get_client_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_client_history()


@router.get("/recent-summary", response_model=RecentSummary)
def get_recent_summary(
    days: int = Query(30, ge=7, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = DashboardService(db)
    return service.get_recent_summary(days)


@router.post("/recalculate-scores")
def recalculate_scores(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    count = calculate_all_scores(db)
    return {"message": f"Scores recalculados para {count} restaurantes"}
