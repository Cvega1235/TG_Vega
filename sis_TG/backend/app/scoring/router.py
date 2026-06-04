from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.scoring.models import ScoringWeightsConfig
from app.scoring.schemas import ScoringWeights, DEFAULT_WEIGHTS
from app.users.models import User

router = APIRouter(prefix="/api/scoring", tags=["scoring"])


def _get_or_default(db: Session) -> ScoringWeights:
    cfg = db.query(ScoringWeightsConfig).filter_by(id=1).first()
    if not cfg:
        return DEFAULT_WEIGHTS
    return ScoringWeights(
        w_cuisine=cfg.w_cuisine,
        w_rating=cfg.w_rating,
        w_reviews=cfg.w_reviews,
        w_zone=cfg.w_zone,
        w_price=cfg.w_price,
        w_completeness=cfg.w_completeness,
    )


@router.get("/weights", response_model=ScoringWeights)
def get_weights(
    db: Session = Depends(get_db),
    _: User = Depends(require_role("viewer")),
):
    return _get_or_default(db)


@router.put("/weights", response_model=ScoringWeights)
def update_weights(
    weights: ScoringWeights,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
):
    cfg = db.query(ScoringWeightsConfig).filter_by(id=1).first()
    if not cfg:
        cfg = ScoringWeightsConfig(id=1)
        db.add(cfg)
    cfg.w_cuisine = weights.w_cuisine
    cfg.w_rating = weights.w_rating
    cfg.w_reviews = weights.w_reviews
    cfg.w_zone = weights.w_zone
    cfg.w_price = weights.w_price
    cfg.w_completeness = weights.w_completeness
    db.commit()
    return weights
