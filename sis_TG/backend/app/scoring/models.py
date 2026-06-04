from sqlalchemy import Column, Integer, Float
from app.database import Base


class ScoringWeightsConfig(Base):
    __tablename__ = "scoring_weights_config"

    id = Column(Integer, primary_key=True, default=1)
    w_cuisine = Column(Float, nullable=False, default=30.0)
    w_rating = Column(Float, nullable=False, default=20.0)
    w_reviews = Column(Float, nullable=False, default=15.0)
    w_zone = Column(Float, nullable=False, default=15.0)
    w_price = Column(Float, nullable=False, default=10.0)
    w_completeness = Column(Float, nullable=False, default=10.0)
