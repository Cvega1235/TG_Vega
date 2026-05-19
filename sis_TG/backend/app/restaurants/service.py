import math
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from fastapi import HTTPException

from app.restaurants.models import (
    Restaurant, RestaurantNote, RestaurantStatusChange, RestaurantScore,
)
from app.users.models import User


VALID_STATUSES = {"nuevo", "contactado", "interesado", "cliente", "no_interesado"}


class RestaurantService:
    def __init__(self, db: Session):
        self.db = db

    def list_restaurants(
        self,
        page: int = 1,
        per_page: int = 20,
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
        min_score: float | None = None,
        prospecto: bool | None = None,
    ) -> dict:
        query = self.db.query(Restaurant).outerjoin(RestaurantScore)

        if fuente:
            query = query.filter(Restaurant.fuente == fuente)
        if zona:
            query = query.filter(Restaurant.zona == zona)
        if status:
            query = query.filter(Restaurant.status == status)
        if rating_min is not None:
            query = query.filter(Restaurant.rating >= rating_min)
        if rating_max is not None:
            query = query.filter(Restaurant.rating <= rating_max)
        if tipo_cocina:
            query = query.filter(Restaurant.tipo_cocina.ilike(f"%{tipo_cocina}%"))
        if search:
            query = query.filter(
                or_(
                    Restaurant.nombre.ilike(f"%{search}%"),
                    Restaurant.direccion.ilike(f"%{search}%"),
                )
            )
        if has_coordinates is True:
            query = query.filter(
                Restaurant.latitud.isnot(None), Restaurant.longitud.isnot(None)
            )
        if tiene_embutidos is not None:
            query = query.filter(Restaurant.tiene_embutidos == tiene_embutidos)
        if min_score is not None:
            query = query.filter(RestaurantScore.total_score >= min_score)
        if prospecto is True:
            query = query.filter(
                Restaurant.status.notin_(["cliente", "no_interesado"])
            )

        # Sorting
        sort_column = getattr(Restaurant, sort_by, Restaurant.id)
        if sort_by == "total_score":
            sort_column = RestaurantScore.total_score
        if sort_order == "desc":
            sort_column = sort_column.desc()
        query = query.order_by(sort_column)

        total = query.count()
        pages = math.ceil(total / per_page) if per_page > 0 else 1
        items = (
            query.options(joinedload(Restaurant.score))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }

    def get_restaurant(self, restaurant_id: int) -> Restaurant:
        restaurant = (
            self.db.query(Restaurant)
            .options(
                joinedload(Restaurant.score),
                joinedload(Restaurant.notes),
                joinedload(Restaurant.status_changes),
            )
            .filter(Restaurant.id == restaurant_id)
            .first()
        )
        if restaurant is None:
            raise HTTPException(status_code=404, detail="Restaurante no encontrado")
        return restaurant

    def update_restaurant(self, restaurant_id: int, data: dict) -> Restaurant:
        restaurant = self.db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if restaurant is None:
            raise HTTPException(status_code=404, detail="Restaurante no encontrado")

        for key, value in data.items():
            if value is not None and hasattr(restaurant, key):
                setattr(restaurant, key, value)

        self.db.commit()
        self.db.refresh(restaurant)
        return restaurant

    def change_status(self, restaurant_id: int, new_status: str, user: User) -> Restaurant:
        if new_status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Estado invalido: {new_status}")

        restaurant = self.db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if restaurant is None:
            raise HTTPException(status_code=404, detail="Restaurante no encontrado")

        old_status = restaurant.status
        restaurant.status = new_status

        change = RestaurantStatusChange(
            restaurant_id=restaurant_id,
            user_id=user.id,
            old_status=old_status,
            new_status=new_status,
        )
        self.db.add(change)
        self.db.commit()
        self.db.refresh(restaurant)
        return restaurant

    def add_note(self, restaurant_id: int, content: str, user: User) -> RestaurantNote:
        restaurant = self.db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
        if restaurant is None:
            raise HTTPException(status_code=404, detail="Restaurante no encontrado")

        note = RestaurantNote(
            restaurant_id=restaurant_id,
            user_id=user.id,
            content=content,
        )
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    def get_notes(self, restaurant_id: int) -> list[dict]:
        notes = (
            self.db.query(RestaurantNote, User.full_name)
            .join(User, RestaurantNote.user_id == User.id)
            .filter(RestaurantNote.restaurant_id == restaurant_id)
            .order_by(RestaurantNote.created_at.desc())
            .all()
        )
        result = []
        for note, user_name in notes:
            result.append({
                "id": note.id,
                "restaurant_id": note.restaurant_id,
                "user_id": str(note.user_id),
                "user_name": user_name,
                "content": note.content,
                "created_at": note.created_at,
            })
        return result

    def delete_note(self, note_id: int, user: User) -> None:
        note = self.db.query(RestaurantNote).filter(RestaurantNote.id == note_id).first()
        if note is None:
            raise HTTPException(status_code=404, detail="Nota no encontrada")
        if str(note.user_id) != str(user.id) and user.role not in ("admin", "superadmin"):
            raise HTTPException(status_code=403, detail="Solo puedes eliminar tus propias notas")
        self.db.delete(note)
        self.db.commit()

    def get_history(self, restaurant_id: int) -> list[dict]:
        changes = (
            self.db.query(RestaurantStatusChange, User.full_name)
            .join(User, RestaurantStatusChange.user_id == User.id)
            .filter(RestaurantStatusChange.restaurant_id == restaurant_id)
            .order_by(RestaurantStatusChange.changed_at.desc())
            .all()
        )
        result = []
        for change, user_name in changes:
            result.append({
                "id": change.id,
                "old_status": change.old_status,
                "new_status": change.new_status,
                "user_name": user_name,
                "changed_at": change.changed_at,
            })
        return result
