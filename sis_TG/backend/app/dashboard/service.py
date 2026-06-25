from datetime import datetime, timezone, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_

from app.restaurants.models import Restaurant, RestaurantScore, RestaurantMLScore, RestaurantStatusChange
from app.dashboard.models import KpiSettings
from app.dashboard.kpi_config import AVG_MONTHLY_REVENUE_PER_CLIENT, THRESHOLDS, PRODUCT_DETAILS

_MESES_ES = {
    1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
}


def _label_mes(dt: datetime) -> str:
    return f"{_MESES_ES[dt.month]} {dt.year}"

_EXCLUDED_CATEGORIES = [
    "panaderia", "panadería",
    "heladeria", "heladería",
    "chocolateria", "chocolatería",
    "dulceria", "dulcería",
    "fruteria", "frutería",
    "jugos", "smoothie",
    "creperia", "crepería",
    "postres",
]


def _exclude_non_prospects(query):
    conditions = []
    for cat in _EXCLUDED_CATEGORIES:
        conditions.append(and_(Restaurant.categoria.isnot(None), func.lower(Restaurant.categoria).contains(cat)))
        conditions.append(and_(Restaurant.tipo_cocina.isnot(None), func.lower(Restaurant.tipo_cocina).contains(cat)))
        conditions.append(func.lower(Restaurant.nombre).contains(cat))
    return query.filter(~or_(*conditions))


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

        in_followup = base(
            self.db.query(func.count(Restaurant.id)).filter(
                Restaurant.status.in_(["contactado", "interesado"])
            )
        ).scalar() or 0

        worked = base(
            self.db.query(func.count(Restaurant.id)).filter(
                Restaurant.status.in_(["contactado", "interesado", "cliente", "no_interesado"])
            )
        ).scalar() or 0
        conversion_rate = round((clients_count / worked * 100), 1) if worked > 0 else 0.0

        start_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_clients_month = (
            base(
                self.db.query(func.count(RestaurantStatusChange.id))
                .filter(
                    RestaurantStatusChange.new_status == "cliente",
                    RestaurantStatusChange.changed_at >= start_of_month,
                )
            ).scalar() or 0
        )

        to_contact = (
            self._fuente_filter(
                self.db.query(func.count(Restaurant.id)).join(RestaurantScore),
                fuente,
            ).filter(
                Restaurant.status == "nuevo",
                RestaurantScore.total_score >= 80,
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
            "in_followup_count": in_followup,
            "conversion_rate": conversion_rate,
            "new_clients_this_month": new_clients_month,
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
                RestaurantMLScore.composite_score,
            )
            .outerjoin(RestaurantScore)
            .outerjoin(RestaurantMLScore, Restaurant.id == RestaurantMLScore.restaurant_id)
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
                "composite_score": float(row[7]) if row[7] else None,
            }
            for row in rows
        ]

    def get_top_prospects(self, limit: int = 3) -> list[dict]:
        query = (
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
        )
        query = _exclude_non_prospects(query)
        rows = (
            query
            .order_by(RestaurantScore.total_score.desc())
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
                "label": _label_mes(row.month),
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
            .limit(6)
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

    def _get_thresholds(self) -> dict:
        row = self.db.query(KpiSettings).first()
        if row:
            return {
                "revenue_green": float(row.revenue_green),
                "revenue_yellow": float(row.revenue_yellow),
                "clients_green": row.clients_green,
                "clients_yellow": row.clients_yellow,
                "new_clients_green": row.new_clients_green,
                "new_clients_yellow": row.new_clients_yellow,
                "max_clients": row.max_clients,
                "max_kg_day": float(row.max_kg_day),
            }
        return {**THRESHOLDS, "max_clients": 72, "max_kg_day": 40.0}

    def get_kpi_settings(self) -> dict:
        return self._get_thresholds()

    def update_kpi_settings(self, data: dict) -> dict:
        row = self.db.query(KpiSettings).first()
        if row is None:
            row = KpiSettings(**data)
            self.db.add(row)
        else:
            for key, value in data.items():
                setattr(row, key, value)
        self.db.commit()
        self.db.refresh(row)
        return self._get_thresholds()

    def get_kpi_evolution(self) -> dict:
        thresholds = self._get_thresholds()
        start_date = datetime.now(timezone.utc) - timedelta(days=365 * 3)

        # Restaurants que alguna vez pasaron a "no_interesado" (pérdida legítima, sin importar estado actual)
        ever_churned_ids = (
            self.db.query(RestaurantStatusChange.restaurant_id)
            .filter(RestaurantStatusChange.new_status == "no_interesado")
            .subquery()
        )

        # Clientes "legítimos": actualmente "cliente" O que alguna vez pasaron a "no_interesado".
        # Excluye los que volvieron directamente a "nuevo/contactado/interesado" sin pasar por "no_interesado" (error de carga).
        legitimate_clients = (
            self.db.query(RestaurantStatusChange.restaurant_id)
            .join(Restaurant, Restaurant.id == RestaurantStatusChange.restaurant_id)
            .filter(
                RestaurantStatusChange.new_status == "cliente",
                or_(
                    Restaurant.status == "cliente",
                    RestaurantStatusChange.restaurant_id.in_(ever_churned_ids),
                ),
            )
            .subquery()
        )

        # Primera conversión a "cliente" de cada cliente legítimo
        first_conversion = (
            self.db.query(
                RestaurantStatusChange.restaurant_id,
                func.min(RestaurantStatusChange.changed_at).label("first_at"),
            )
            .filter(
                RestaurantStatusChange.new_status == "cliente",
                RestaurantStatusChange.restaurant_id.in_(legitimate_clients),
            )
            .group_by(RestaurantStatusChange.restaurant_id)
            .subquery()
        )

        gained_rows = (
            self.db.query(
                func.date_trunc("month", first_conversion.c.first_at).label("month"),
                func.count().label("new_clients"),
            )
            .filter(first_conversion.c.first_at >= start_date)
            .group_by("month")
            .order_by("month")
            .all()
        )

        # Ingresos de clientes legítimos agrupados por su mes de incorporación
        revenue_gained_rows = (
            self.db.query(
                RestaurantStatusChange.restaurant_id,
                func.min(RestaurantStatusChange.changed_at).label("first_at"),
                func.coalesce(Restaurant.monthly_revenue, AVG_MONTHLY_REVENUE_PER_CLIENT).label("revenue"),
            )
            .join(Restaurant, Restaurant.id == RestaurantStatusChange.restaurant_id)
            .filter(
                RestaurantStatusChange.new_status == "cliente",
                RestaurantStatusChange.changed_at >= start_date,
                RestaurantStatusChange.restaurant_id.in_(legitimate_clients),
            )
            .group_by(RestaurantStatusChange.restaurant_id, Restaurant.monthly_revenue)
            .all()
        )
        revenue_gained_by_month: dict = {}
        for row in revenue_gained_rows:
            key = row.first_at.strftime("%Y-%m")
            revenue_gained_by_month[key] = revenue_gained_by_month.get(key, 0.0) + float(row.revenue)

        # Pérdidas reales: pasaron a "no_interesado" siendo clientes legítimos
        lost_rows = (
            self.db.query(
                func.date_trunc("month", RestaurantStatusChange.changed_at).label("month"),
                func.count().label("lost_clients"),
            )
            .filter(
                RestaurantStatusChange.new_status == "no_interesado",
                RestaurantStatusChange.changed_at >= start_date,
                RestaurantStatusChange.restaurant_id.in_(legitimate_clients),
            )
            .group_by("month")
            .order_by("month")
            .all()
        )

        revenue_lost_rows = (
            self.db.query(
                RestaurantStatusChange.changed_at,
                func.coalesce(Restaurant.monthly_revenue, AVG_MONTHLY_REVENUE_PER_CLIENT).label("revenue"),
            )
            .join(Restaurant, Restaurant.id == RestaurantStatusChange.restaurant_id)
            .filter(
                RestaurantStatusChange.new_status == "no_interesado",
                RestaurantStatusChange.changed_at >= start_date,
                RestaurantStatusChange.restaurant_id.in_(legitimate_clients),
            )
            .all()
        )
        revenue_lost_by_month: dict = {}
        for row in revenue_lost_rows:
            key = row.changed_at.strftime("%Y-%m")
            revenue_lost_by_month[key] = revenue_lost_by_month.get(key, 0.0) + float(row.revenue)

        lost_by_month = {row.month: row.lost_clients for row in lost_rows}

        all_months = sorted(set(
            [row.month for row in gained_rows] + list(lost_by_month.keys())
        ))
        gained_by_month = {row.month: row.new_clients for row in gained_rows}

        cumulative = 0
        cumulative_revenue = 0.0
        monthly = []
        for month_dt in all_months:
            new_clients = gained_by_month.get(month_dt, 0)
            lost_clients = lost_by_month.get(month_dt, 0)
            month_key = month_dt.strftime("%Y-%m")
            revenue_gained = round(revenue_gained_by_month.get(month_key, 0.0), 2)
            revenue_lost = round(revenue_lost_by_month.get(month_key, 0.0), 2)
            cumulative = cumulative + new_clients - lost_clients
            cumulative_revenue = max(0.0, cumulative_revenue + revenue_gained - revenue_lost)
            estimated_revenue = round(cumulative_revenue, 2)

            traffic_clients = (
                "green" if cumulative >= thresholds["clients_green"]
                else "yellow" if cumulative >= thresholds["clients_yellow"]
                else "red"
            )
            traffic_revenue = (
                "green" if estimated_revenue >= thresholds["revenue_green"]
                else "yellow" if estimated_revenue >= thresholds["revenue_yellow"]
                else "red"
            )

            monthly.append({
                "month": month_dt.strftime("%Y-%m"),
                "label": _label_mes(month_dt),
                "new_clients": new_clients,
                "lost_clients": lost_clients,
                "cumulative_clients": cumulative,
                "revenue_gained": revenue_gained,
                "revenue_lost": revenue_lost,
                "estimated_revenue": estimated_revenue,
                "traffic_clients": traffic_clients,
                "traffic_revenue": traffic_revenue,
            })

        actual_total_revenue = (
            self.db.query(func.sum(Restaurant.monthly_revenue))
            .filter(
                Restaurant.status == "cliente",
                Restaurant.monthly_revenue.isnot(None),
            )
            .scalar()
        )

        actual_total_clients = (
            self.db.query(func.count(Restaurant.id))
            .filter(Restaurant.status == "cliente")
            .scalar() or 0
        )

        return {
            "monthly": monthly,
            "avg_revenue_per_client": AVG_MONTHLY_REVENUE_PER_CLIENT,
            "thresholds": thresholds,
            "product_details": PRODUCT_DETAILS,
            "actual_total_revenue": float(actual_total_revenue) if actual_total_revenue else None,
            "actual_total_clients": actual_total_clients,
        }

    def get_clients_by_month(self, month: str) -> list[dict]:
        try:
            month_dt = datetime.strptime(month, "%Y-%m").replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de mes invalido. Usa YYYY-MM")

        next_month = (month_dt + timedelta(days=32)).replace(day=1)

        first_conversion = (
            self.db.query(
                RestaurantStatusChange.restaurant_id,
                func.min(RestaurantStatusChange.changed_at).label("first_at"),
            )
            .filter(RestaurantStatusChange.new_status == "cliente")
            .group_by(RestaurantStatusChange.restaurant_id)
            .subquery()
        )

        rows = (
            self.db.query(
                Restaurant.id,
                Restaurant.nombre,
                Restaurant.zona,
                Restaurant.tipo_cocina,
                Restaurant.telefono,
                Restaurant.monthly_revenue,
                first_conversion.c.first_at,
            )
            .join(first_conversion, Restaurant.id == first_conversion.c.restaurant_id)
            .filter(
                first_conversion.c.first_at >= month_dt,
                first_conversion.c.first_at < next_month,
            )
            .order_by(Restaurant.monthly_revenue.desc().nullslast())
            .all()
        )

        return [
            {
                "id": row[0],
                "nombre": row[1],
                "zona": row[2],
                "tipo_cocina": row[3],
                "telefono": row[4],
                "monthly_revenue": float(row[5]) if row[5] is not None else None,
                "converted_at": row[6].isoformat(),
            }
            for row in rows
        ]

    def get_recent_summary(self, days: int = 30) -> dict:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        new_restaurants = (
            self.db.query(func.count(Restaurant.id))
            .filter(Restaurant.created_at >= cutoff)
            .scalar() or 0
        )

        new_high_score = (
            self.db.query(func.count(Restaurant.id))
            .join(RestaurantMLScore, Restaurant.id == RestaurantMLScore.restaurant_id)
            .filter(
                Restaurant.created_at >= cutoff,
                RestaurantMLScore.composite_score >= 60,
                Restaurant.status == "nuevo",
            )
            .scalar() or 0
        )

        new_clients = (
            self.db.query(func.count(RestaurantStatusChange.id))
            .filter(
                RestaurantStatusChange.new_status == "cliente",
                RestaurantStatusChange.changed_at >= cutoff,
            )
            .scalar() or 0
        )

        last_scraped = (
            self.db.query(func.max(Restaurant.scraped_at)).scalar()
        )

        return {
            "days": days,
            "new_restaurants": new_restaurants,
            "new_high_score_prospects": new_high_score,
            "new_clients": new_clients,
            "last_scraped_at": last_scraped.isoformat() if last_scraped else None,
        }

    def get_top_scores(self, limit: int = 15) -> list[dict]:
        query = (
            self.db.query(
                Restaurant.id, Restaurant.nombre, Restaurant.zona,
                Restaurant.fuente, Restaurant.rating, Restaurant.status,
                RestaurantScore.total_score, Restaurant.tipo_cocina,
                Restaurant.tiene_embutidos,
            )
            .join(RestaurantMLScore, Restaurant.id == RestaurantMLScore.restaurant_id)
            .outerjoin(RestaurantScore, Restaurant.id == RestaurantScore.restaurant_id)
            .filter(Restaurant.status.notin_(["cliente", "no_interesado"]))
        )
        query = _exclude_non_prospects(query)
        rows = (
            query
            .order_by(RestaurantScore.total_score.desc().nulls_last())
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
                "total_score": float(row[6]) if row[6] else 0.0,
                "tipo_cocina": row[7],
                "tiene_embutidos": row[8],
            }
            for row in rows
        ]
