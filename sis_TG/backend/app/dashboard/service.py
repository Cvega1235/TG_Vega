from datetime import datetime, timezone, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.restaurants.models import Restaurant, RestaurantScore, RestaurantMLScore, RestaurantStatusChange


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def _fuente_filter(self, q, fuente: str | None):
        if fuente:
            q = q.filter(Restaurant.fuente == fuente)
        return q

    def get_stats(self, fuente: str | None = None) -> dict:
        base = lambda q: self._fuente_filter(q, fuente)  # noqa: E731

        total = base(self.db.query(func.count(Restaurant.id))).scalar() or 0
        avg_rating = base(
            self.db.query(func.avg(Restaurant.rating)).filter(Restaurant.rating.isnot(None))
        ).scalar()

        high_affinity = (
            self._fuente_filter(
                self.db.query(func.count(RestaurantMLScore.id))
                .join(Restaurant, Restaurant.id == RestaurantMLScore.restaurant_id),
                fuente,
            ).filter(RestaurantMLScore.composite_score >= 70).scalar() or 0
        )

        clients_count = base(
            self.db.query(func.count(Restaurant.id)).filter(Restaurant.status == "cliente")
        ).scalar() or 0

        with_embutidos = base(
            self.db.query(func.count(Restaurant.id)).filter(
                Restaurant.tiene_embutidos == True  # noqa: E712
            )
        ).scalar() or 0

        to_contact = (
            self._fuente_filter(
                self.db.query(func.count(Restaurant.id)).join(RestaurantMLScore),
                fuente,
            ).filter(
                Restaurant.status == "nuevo",
                RestaurantMLScore.composite_score >= 60,
            ).scalar() or 0
        )

        status_rows = (
            base(self.db.query(Restaurant.status, func.count(Restaurant.id)))
            .group_by(Restaurant.status)
            .all()
        )
        status_counts = {row[0]: row[1] for row in status_rows}

        source_rows = (
            self.db.query(Restaurant.fuente, func.count(Restaurant.id))
            .group_by(Restaurant.fuente)
            .all()
        )
        source_counts = {row[0]: row[1] for row in source_rows}

        with_coordinates = base(
            self.db.query(func.count(Restaurant.id)).filter(
                Restaurant.latitud.isnot(None),
                Restaurant.longitud.isnot(None),
            )
        ).scalar() or 0

        with_phone = base(
            self.db.query(func.count(Restaurant.id)).filter(
                Restaurant.telefono.isnot(None),
                Restaurant.telefono != "",
            )
        ).scalar() or 0

        return {
            "total_restaurants": total,
            "avg_rating": round(float(avg_rating), 2) if avg_rating else None,
            "high_affinity_count": high_affinity,
            "clients_count": clients_count,
            "with_embutidos_count": with_embutidos,
            "to_contact_count": to_contact,
            "total_with_coordinates": with_coordinates,
            "total_with_phone": with_phone,
            "status_counts": status_counts,
            "source_counts": source_counts,
        }

    def get_by_zone(self, fuente: str | None = None) -> list[dict]:
        rows = (
            self._fuente_filter(
                self.db.query(Restaurant.zona, func.count(Restaurant.id))
                .filter(Restaurant.zona.isnot(None)),
                fuente,
            )
            .group_by(Restaurant.zona)
            .order_by(func.count(Restaurant.id).desc())
            .all()
        )
        return [{"label": row[0], "value": row[1]} for row in rows]

    def get_by_rating(self, fuente: str | None = None) -> list[dict]:
        ranges = [
            ("0-1", 0, 1),
            ("1-2", 1, 2),
            ("2-3", 2, 3),
            ("3-4", 3, 4),
            ("4-5", 4, 5.1),
        ]
        result = []
        for label, low, high in ranges:
            count = (
                self._fuente_filter(
                    self.db.query(func.count(Restaurant.id))
                    .filter(Restaurant.rating >= low, Restaurant.rating < high),
                    fuente,
                ).scalar()
            ) or 0
            result.append({"label": label, "value": count})
        return result

    def get_by_cuisine(self, fuente: str | None = None) -> list[dict]:
        rows = (
            self._fuente_filter(
                self.db.query(Restaurant.tipo_cocina, func.count(Restaurant.id))
                .filter(Restaurant.tipo_cocina.isnot(None), Restaurant.tipo_cocina != ""),
                fuente,
            )
            .group_by(Restaurant.tipo_cocina)
            .order_by(func.count(Restaurant.id).desc())
            .limit(15)
            .all()
        )
        return [{"label": row[0], "value": row[1]} for row in rows]

    def get_by_source(self) -> list[dict]:
        rows = (
            self.db.query(Restaurant.fuente, func.count(Restaurant.id))
            .group_by(Restaurant.fuente)
            .all()
        )
        return [{"label": row[0], "value": row[1]} for row in rows]

    def get_by_status(self, fuente: str | None = None) -> list[dict]:
        rows = (
            self._fuente_filter(
                self.db.query(Restaurant.status, func.count(Restaurant.id)),
                fuente,
            )
            .group_by(Restaurant.status)
            .all()
        )
        return [{"label": row[0], "value": row[1]} for row in rows]

    def get_map_data(self) -> list[dict]:
        rows = (
            self.db.query(
                Restaurant.id, Restaurant.nombre, Restaurant.latitud,
                Restaurant.longitud, Restaurant.rating, Restaurant.status,
                RestaurantScore.total_score,
            )
            .outerjoin(RestaurantScore)
            .filter(Restaurant.latitud.isnot(None), Restaurant.longitud.isnot(None))
            .all()
        )
        return [
            {
                "id": row[0],
                "nombre": row[1],
                "latitud": float(row[2]),
                "longitud": float(row[3]),
                "rating": float(row[4]) if row[4] else None,
                "status": row[5],
                "total_score": float(row[6]) if row[6] else None,
            }
            for row in rows
        ]

    def get_top_prospects(self, limit: int = 3) -> list[dict]:
        rows = (
            self.db.query(
                Restaurant.id, Restaurant.nombre, Restaurant.zona,
                Restaurant.tipo_cocina, Restaurant.rating, Restaurant.status,
                Restaurant.telefono, Restaurant.tiene_embutidos,
                RestaurantScore.total_score,
                RestaurantScore.cuisine_score,
                RestaurantScore.rating_score,
                RestaurantScore.reviews_score,
                RestaurantScore.zone_score,
                RestaurantMLScore.composite_score,
            )
            .join(RestaurantScore)
            .outerjoin(RestaurantMLScore, Restaurant.id == RestaurantMLScore.restaurant_id)
            .filter(Restaurant.status.notin_(["cliente", "no_interesado"]))
            .order_by(func.coalesce(RestaurantMLScore.composite_score, RestaurantScore.total_score).desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": row[0],
                "nombre": row[1],
                "zona": row[2],
                "tipo_cocina": row[3],
                "rating": float(row[4]) if row[4] else None,
                "status": row[5],
                "telefono": row[6],
                "tiene_embutidos": row[7],
                "total_score": float(row[13]) if row[13] is not None else float(row[8]),
                "cuisine_score": float(row[9]) if row[9] else None,
                "rating_score": float(row[10]) if row[10] else None,
                "reviews_score": float(row[11]) if row[11] else None,
                "zone_score": float(row[12]) if row[12] else None,
                "score_source": "ml" if row[13] is not None else "icp",
            }
            for row in rows
        ]

    def get_client_history(self) -> dict:
        start_date = datetime.now(timezone.utc) - timedelta(days=365)

        monthly_rows = (
            self.db.query(
                func.date_trunc("month", RestaurantStatusChange.changed_at).label("month"),
                func.count().label("count"),
            )
            .filter(
                RestaurantStatusChange.new_status == "cliente",
                RestaurantStatusChange.changed_at >= start_date,
            )
            .group_by("month")
            .order_by("month")
            .all()
        )

        monthly = [
            {
                "month": row.month.strftime("%Y-%m"),
                "label": row.month.strftime("%b %Y"),
                "count": row.count,
            }
            for row in monthly_rows
        ]

        recent_rows = (
            self.db.query(
                Restaurant.id,
                Restaurant.nombre,
                Restaurant.zona,
                Restaurant.tipo_cocina,
                RestaurantStatusChange.changed_at,
            )
            .join(RestaurantStatusChange, Restaurant.id == RestaurantStatusChange.restaurant_id)
            .filter(RestaurantStatusChange.new_status == "cliente")
            .order_by(RestaurantStatusChange.changed_at.desc())
            .limit(5)
            .all()
        )

        recent_conversions = [
            {
                "id": row[0],
                "nombre": row[1],
                "zona": row[2],
                "tipo_cocina": row[3],
                "converted_at": row[4].isoformat(),
            }
            for row in recent_rows
        ]

        total_clients = self.db.query(func.count(Restaurant.id)).filter(
            Restaurant.status == "cliente"
        ).scalar() or 0

        last_month_start = datetime.now(timezone.utc).replace(day=1)
        new_this_month = (
            self.db.query(func.count(RestaurantStatusChange.id))
            .filter(
                RestaurantStatusChange.new_status == "cliente",
                RestaurantStatusChange.changed_at >= last_month_start,
            )
            .scalar() or 0
        )

        return {
            "monthly": monthly,
            "recent_conversions": recent_conversions,
            "total_clients": total_clients,
            "new_this_month": new_this_month,
        }

    def get_top_scores(self, limit: int = 15) -> list[dict]:
        rows = (
            self.db.query(
                Restaurant.id, Restaurant.nombre, Restaurant.zona,
                Restaurant.fuente, Restaurant.rating, Restaurant.status,
                RestaurantScore.total_score, Restaurant.tipo_cocina,
                Restaurant.tiene_embutidos,
                RestaurantMLScore.composite_score,
            )
            .join(RestaurantScore)
            .outerjoin(RestaurantMLScore, Restaurant.id == RestaurantMLScore.restaurant_id)
            .order_by(func.coalesce(RestaurantMLScore.composite_score, RestaurantScore.total_score).desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "id": row[0],
                "nombre": row[1],
                "zona": row[2],
                "fuente": row[3],
                "rating": float(row[4]) if row[4] else None,
                "status": row[5],
                "total_score": float(row[9]) if row[9] is not None else float(row[6]),
                "tipo_cocina": row[7],
                "tiene_embutidos": row[8],
            }
            for row in rows
        ]
