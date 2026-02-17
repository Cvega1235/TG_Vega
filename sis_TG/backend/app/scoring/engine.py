import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.restaurants.models import Restaurant, RestaurantScore
from app.scoring.config import (
    CUISINE_AFFINITY, ZONE_SCORES, PRICE_SCORES,
    DEFAULT_ZONE_SCORE, DEFAULT_PRICE_SCORE, DEFAULT_CUISINE_AFFINITY,
)


def _cuisine_affinity_score(tipo_cocina: str | None, categoria: str | None) -> float:
    """Score 0-30 based on how much the cuisine uses embutidos."""
    max_affinity = DEFAULT_CUISINE_AFFINITY

    texts = []
    if tipo_cocina:
        texts.append(tipo_cocina.lower())
    if categoria:
        texts.append(categoria.lower())

    combined = " ".join(texts)
    for keyword, affinity in CUISINE_AFFINITY.items():
        if keyword in combined:
            max_affinity = max(max_affinity, affinity)

    return round(max_affinity * 30.0, 2)


def _rating_score(rating: float | None) -> float:
    """Score 0-20 based on restaurant rating."""
    if rating is None:
        return 10.0
    if rating >= 4.5:
        return 20.0
    elif rating >= 4.0:
        return 17.0
    elif rating >= 3.5:
        return 13.0
    elif rating >= 3.0:
        return 9.0
    elif rating >= 2.0:
        return 5.0
    else:
        return 2.0


def _reviews_score(num_resenas: int | None) -> float:
    """Score 0-15 based on review volume (logarithmic)."""
    if num_resenas is None or num_resenas == 0:
        return 3.0
    raw = math.log10(num_resenas + 1) / math.log10(1001)
    return round(min(raw * 15.0, 15.0), 2)


def _zone_score(zona: str | None, direccion: str | None) -> float:
    """Score 0-15 based on neighborhood economic profile."""
    if zona:
        for zone_name, score in ZONE_SCORES.items():
            if zone_name.lower() in zona.lower():
                return score

    if direccion:
        dir_lower = direccion.lower()
        for zone_name, score in ZONE_SCORES.items():
            if zone_name.lower() in dir_lower:
                return score

    return DEFAULT_ZONE_SCORE


def _price_score(precio: str | None) -> float:
    """Score 0-10 based on price level."""
    if precio is None:
        return DEFAULT_PRICE_SCORE
    return PRICE_SCORES.get(precio.strip(), DEFAULT_PRICE_SCORE)


def _completeness_score(restaurant: Restaurant) -> float:
    """Score 0-10 based on data completeness (ease of contact)."""
    score = 0.0
    if restaurant.telefono:
        score += 3.0
    if restaurant.direccion:
        score += 2.0
    if restaurant.latitud is not None and restaurant.longitud is not None:
        score += 2.0
    if restaurant.tipo_cocina:
        score += 1.0
    if restaurant.precio:
        score += 1.0
    if restaurant.num_resenas and restaurant.num_resenas > 0:
        score += 1.0
    return score


def compute_score(restaurant: Restaurant) -> dict:
    """Compute client potential score (0-100) for a restaurant."""
    cs = _cuisine_affinity_score(restaurant.tipo_cocina, restaurant.categoria)
    rs = _rating_score(float(restaurant.rating) if restaurant.rating is not None else None)
    rv = _reviews_score(restaurant.num_resenas)
    zs = _zone_score(restaurant.zona, restaurant.direccion)
    ps = _price_score(restaurant.precio)
    ds = _completeness_score(restaurant)

    total = cs + rs + rv + zs + ps + ds

    return {
        "total_score": round(total, 2),
        "cuisine_score": cs,
        "rating_score": rs,
        "reviews_score": rv,
        "zone_score": zs,
        "price_score": ps,
        "completeness_score": ds,
    }


def calculate_all_scores(db: Session) -> int:
    """Recalculate scores for all restaurants. Returns count."""
    restaurants = db.query(Restaurant).all()
    count = 0

    for restaurant in restaurants:
        scores = compute_score(restaurant)

        existing = (
            db.query(RestaurantScore)
            .filter(RestaurantScore.restaurant_id == restaurant.id)
            .first()
        )

        if existing:
            for key, value in scores.items():
                setattr(existing, key, value)
            existing.calculated_at = datetime.now(timezone.utc)
        else:
            score_obj = RestaurantScore(
                restaurant_id=restaurant.id,
                calculated_at=datetime.now(timezone.utc),
                **scores,
            )
            db.add(score_obj)

        count += 1

    db.commit()
    return count
