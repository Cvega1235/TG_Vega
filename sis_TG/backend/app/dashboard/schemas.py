from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_restaurants: int
    avg_rating: float | None
    total_with_coordinates: int
    total_with_phone: int
    status_counts: dict[str, int]
    source_counts: dict[str, int]


class ChartDataPoint(BaseModel):
    label: str
    value: int | float


class MapDataPoint(BaseModel):
    id: int
    nombre: str
    latitud: float
    longitud: float
    rating: float | None = None
    status: str
    total_score: float | None = None


class TopScoredItem(BaseModel):
    id: int
    nombre: str
    zona: str | None = None
    fuente: str
    rating: float | None = None
    status: str
    total_score: float

    model_config = {"from_attributes": True}
