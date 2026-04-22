from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user, require_role
from app.users.models import User
from app.restaurants.schemas import (
    RestaurantWithScore, RestaurantUpdate, StatusUpdate,
    NoteCreate, NoteResponse, StatusChangeResponse,
    PaginatedRestaurants,
)
from app.restaurants.service import RestaurantService
from app.restaurants.models import Restaurant
from app.restaurants.menu_analyzer import run_analysis

router = APIRouter(prefix="/api/restaurants", tags=["restaurants"])


@router.post("/menu-analysis/run")
def run_menu_analysis(
    force: bool = Query(False, description="Re-analizar restaurantes ya procesados"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """Ejecuta el análisis de afinidad de productos Don Piotr sobre todos
    los restaurantes. Por defecto solo procesa los no analizados aún."""
    return run_analysis(db, force=force)


@router.get("/menu-analysis/summary")
def menu_analysis_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    """Resumen del análisis de menús: cuántos restaurantes usan embutidos."""
    total = db.query(func.count(Restaurant.id)).scalar()
    analizados = db.query(func.count(Restaurant.id)).filter(
        Restaurant.menu_analizado_at.isnot(None)
    ).scalar()
    con_embutidos = db.query(func.count(Restaurant.id)).filter(
        Restaurant.tiene_embutidos == True  # noqa: E712
    ).scalar()
    sin_embutidos = db.query(func.count(Restaurant.id)).filter(
        Restaurant.tiene_embutidos == False  # noqa: E712
    ).scalar()

    # Top productos detectados
    rows = db.query(Restaurant.productos_detectados).filter(
        Restaurant.productos_detectados.isnot(None),
        Restaurant.productos_detectados != "",
    ).all()

    conteo_productos: dict[str, int] = {}
    for (productos_str,) in rows:
        for prod in productos_str.split(", "):
            prod = prod.strip()
            if prod:
                conteo_productos[prod] = conteo_productos.get(prod, 0) + 1

    top_productos = sorted(
        [{"producto": k, "count": v} for k, v in conteo_productos.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    return {
        "total_restaurantes": total,
        "total_analizados": analizados,
        "con_embutidos": con_embutidos,
        "sin_embutidos": sin_embutidos,
        "porcentaje_con_embutidos": round(con_embutidos / analizados * 100, 1) if analizados else 0,
        "top_productos": top_productos[:10],
    }


@router.get("", response_model=PaginatedRestaurants)
def list_restaurants(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    fuente: str | None = None,
    zona: str | None = None,
    status: str | None = None,
    rating_min: float | None = None,
    rating_max: float | None = None,
    tipo_cocina: str | None = None,
    search: str | None = None,
    sort_by: str = "id",
    sort_order: str = "asc",
    has_coordinates: bool | None = None,
    tiene_embutidos: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = RestaurantService(db)
    return service.list_restaurants(
        page=page, per_page=per_page, fuente=fuente, zona=zona,
        status=status, rating_min=rating_min, rating_max=rating_max,
        tipo_cocina=tipo_cocina, search=search, sort_by=sort_by,
        sort_order=sort_order, has_coordinates=has_coordinates,
        tiene_embutidos=tiene_embutidos,
    )


@router.get("/{restaurant_id}", response_model=RestaurantWithScore)
def get_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = RestaurantService(db)
    return service.get_restaurant(restaurant_id)


@router.put("/{restaurant_id}", response_model=RestaurantWithScore)
def update_restaurant(
    restaurant_id: int,
    data: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analista")),
):
    service = RestaurantService(db)
    return service.update_restaurant(restaurant_id, data.model_dump(exclude_unset=True))


@router.put("/{restaurant_id}/status", response_model=RestaurantWithScore)
def change_status(
    restaurant_id: int,
    data: StatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analista")),
):
    service = RestaurantService(db)
    return service.change_status(restaurant_id, data.status, current_user)


@router.post("/{restaurant_id}/notes", response_model=NoteResponse, status_code=201)
def add_note(
    restaurant_id: int,
    data: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analista")),
):
    service = RestaurantService(db)
    note = service.add_note(restaurant_id, data.content, current_user)
    return {
        "id": note.id,
        "restaurant_id": note.restaurant_id,
        "user_id": str(note.user_id),
        "user_name": current_user.full_name,
        "content": note.content,
        "created_at": note.created_at,
    }


@router.get("/{restaurant_id}/notes", response_model=list[NoteResponse])
def get_notes(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = RestaurantService(db)
    return service.get_notes(restaurant_id)


@router.delete("/{restaurant_id}/notes/{note_id}", status_code=204)
def delete_note(
    restaurant_id: int,
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("analista")),
):
    service = RestaurantService(db)
    service.delete_note(note_id, current_user)


@router.get("/{restaurant_id}/history", response_model=list[StatusChangeResponse])
def get_history(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = RestaurantService(db)
    return service.get_history(restaurant_id)
