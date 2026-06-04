from pydantic import BaseModel, model_validator


class ScoringWeights(BaseModel):
    w_cuisine: float
    w_rating: float
    w_reviews: float
    w_zone: float
    w_price: float
    w_completeness: float

    @model_validator(mode="after")
    def check_sum(self):
        total = (
            self.w_cuisine + self.w_rating + self.w_reviews
            + self.w_zone + self.w_price + self.w_completeness
        )
        if abs(total - 100.0) > 0.1:
            raise ValueError(f"Los pesos deben sumar 100. Suma actual: {total:.2f}")
        return self


DEFAULT_WEIGHTS = ScoringWeights(
    w_cuisine=30.0,
    w_rating=20.0,
    w_reviews=15.0,
    w_zone=15.0,
    w_price=10.0,
    w_completeness=10.0,
)
