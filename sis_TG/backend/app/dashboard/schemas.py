from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_restaurants: int
    avg_rating: float | None
    high_affinity_count: int
    clients_count: int
    with_embutidos_count: int
    to_contact_count: int
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
    tipo_cocina: str | None = None
    tiene_embutidos: bool | None = None

    model_config = {"from_attributes": True}


class TopProspectItem(BaseModel):
    id: int
    nombre: str
    zona: str | None = None
    tipo_cocina: str | None = None
    rating: float | None = None
    status: str
    telefono: str | None = None
    tiene_embutidos: bool | None = None
    total_score: float
    cuisine_score: float | None = None
    rating_score: float | None = None
    reviews_score: float | None = None
    zone_score: float | None = None

    model_config = {"from_attributes": True}
