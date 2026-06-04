import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.restaurants.models import Restaurant, RestaurantScore
from app.scoring.config import (
    CUISINE_AFFINITY, ZONE_SCORES, PRICE_SCORES,
    DEFAULT_ZONE_SCORE, DEFAULT_PRICE_SCORE, DEFAULT_CUISINE_AFFINITY,
)
from app.scoring.schemas import ScoringWeights, DEFAULT_WEIGHTS


def _cuisine_affinity_score(tipo_cocina: str | None, categoria: str | None, max_score: float = 30.0) -> float:
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
    return round(max_affinity * max_score, 2)


def _rating_score(rating: float | None, max_score: float = 20.0) -> float:
    scale = max_score / 20.0
    if rating is None:
        return round(10.0 * scale, 2)
    if rating >= 4.5:
        return round(20.0 * scale, 2)
    elif rating >= 4.0:
        return round(17.0 * scale, 2)
    elif rating >= 3.5:
        return round(13.0 * scale, 2)
    elif rating >= 3.0:
        return round(9.0 * scale, 2)
    elif rating >= 2.0:
        return round(5.0 * scale, 2)
    else:
        return round(2.0 * scale, 2)


def _reviews_score(num_resenas: int | None, max_score: float = 15.0) -> float:
    if num_resenas is None or num_resenas == 0:
        return round(3.0 * (max_score / 15.0), 2)
    raw = math.log10(num_resenas + 1) / math.log10(1001)
    return round(min(raw * max_score, max_score), 2)


def _zone_score(zona: str | None, direccion: str | None, max_score: float = 15.0) -> float:
    scale = max_score / 15.0
    if zona:
        for zone_name, score in ZONE_SCORES.items():
            if zone_name.lower() in zona.lower():
                return round(score * scale, 2)
    if direccion:
        dir_lower = direccion.lower()
        for zone_name, score in ZONE_SCORES.items():
            if zone_name.lower() in dir_lower:
                return round(score * scale, 2)
    return round(DEFAULT_ZONE_SCORE * scale, 2)


def _price_score(precio: str | None, max_score: float = 10.0) -> float:
    scale = max_score / 10.0
    if precio is None:
        return round(DEFAULT_PRICE_SCORE * scale, 2)
    raw = PRICE_SCORES.get(precio.strip(), DEFAULT_PRICE_SCORE)
    return round(raw * scale, 2)


def _completeness_score(restaurant: Restaurant, max_score: float = 10.0) -> float:
    scale = max_score / 10.0
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
    return round(score * scale, 2)


def compute_score(restaurant: Restaurant, weights: ScoringWeights | None = None) -> dict:
    w = weights or DEFAULT_WEIGHTS
    cs = _cuisine_affinity_score(restaurant.tipo_cocina, restaurant.categoria, w.w_cuisine)
    rs = _rating_score(float(restaurant.rating) if restaurant.rating is not None else None, w.w_rating)
    rv = _reviews_score(restaurant.num_resenas, w.w_reviews)
    zs = _zone_score(restaurant.zona, restaurant.direccion, w.w_zone)
    ps = _price_score(restaurant.precio, w.w_price)
    ds = _completeness_score(restaurant, w.w_completeness)
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
    from app.scoring.models import ScoringWeightsConfig
    from app.scoring.schemas import ScoringWeights

    cfg = db.query(ScoringWeightsConfig).filter_by(id=1).first()
    weights = None
    if cfg:
        weights = ScoringWeights(
            w_cuisine=cfg.w_cuisine,
            w_rating=cfg.w_rating,
            w_reviews=cfg.w_reviews,
            w_zone=cfg.w_zone,
            w_price=cfg.w_price,
            w_completeness=cfg.w_completeness,
        )

    restaurants = db.query(Restaurant).all()
    count = 0

    for restaurant in restaurants:
        scores = compute_score(restaurant, weights)
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
