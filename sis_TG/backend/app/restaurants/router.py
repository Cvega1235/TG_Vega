from fastapi import APIRouter, Depends, Query
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

router = APIRouter(prefix="/api/restaurants", tags=["restaurants"])


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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("viewer")),
):
    service = RestaurantService(db)
    return service.list_restaurants(
        page=page, per_page=per_page, fuente=fuente, zona=zona,
        status=status, rating_min=rating_min, rating_max=rating_max,
        tipo_cocina=tipo_cocina, search=search, sort_by=sort_by,
        sort_order=sort_order, has_coordinates=has_coordinates,
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
