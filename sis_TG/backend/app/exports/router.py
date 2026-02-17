from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
import io

from app.database import get_db
from app.auth.dependencies import require_role
from app.users.models import User
from app.exports.service import export_csv, export_excel, export_pdf

router = APIRouter(prefix="/api/exports", tags=["exports"])


def _get_filters(
    fuente: str | None = None,
    zona: str | None = None,
    status: str | None = None,
    rating_min: float | None = None,
    rating_max: float | None = None,
    search: str | None = None,
) -> dict:
    return {
        "fuente": fuente,
        "zona": zona,
        "status": status,
        "rating_min": rating_min,
        "rating_max": rating_max,
        "search": search,
    }


@router.get("/csv")
def download_csv(
    fuente: str | None = None,
    zona: str | None = None,
    status: str | None = None,
    rating_min: float | None = None,
    rating_max: float | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analista")),
):
    filters = _get_filters(fuente, zona, status, rating_min, rating_max, search)
    content = export_csv(db, **filters)
    return StreamingResponse(
        io.StringIO(content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=restaurantes_don_piotr.csv"},
    )


@router.get("/excel")
def download_excel(
    fuente: str | None = None,
    zona: str | None = None,
    status: str | None = None,
    rating_min: float | None = None,
    rating_max: float | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analista")),
):
    filters = _get_filters(fuente, zona, status, rating_min, rating_max, search)
    content = export_excel(db, **filters)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=restaurantes_don_piotr.xlsx"},
    )


@router.get("/pdf")
def download_pdf(
    fuente: str | None = None,
    zona: str | None = None,
    status: str | None = None,
    rating_min: float | None = None,
    rating_max: float | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analista")),
):
    filters = _get_filters(fuente, zona, status, rating_min, rating_max, search)
    content = export_pdf(db, **filters)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=restaurantes_don_piotr.pdf"},
    )
