from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_restaurants: int
    avg_rating: float | None
    high_affinity_count: int
    clients_count: int
    in_followup_count: int
    conversion_rate: float
    new_clients_this_month: int
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
    score_source: str = "icp"

    model_config = {"from_attributes": True}


class MonthlyConversion(BaseModel):
    month: str
    label: str
    count: int


class RecentConversion(BaseModel):
    id: int
    nombre: str
    zona: str | None = None
    tipo_cocina: str | None = None
    converted_at: str


class ClientHistoryData(BaseModel):
    monthly: list[MonthlyConversion]
    recent_conversions: list[RecentConversion]
    total_clients: int
    new_this_month: int


class RecentSummary(BaseModel):
    days: int
    new_restaurants: int
    new_high_score_prospects: int
    new_clients: int
    last_scraped_at: str | None = None


class MonthlyKpiPoint(BaseModel):
    month: str
    label: str
    new_clients: int
    lost_clients: int
    cumulative_clients: int
    estimated_revenue: float
    traffic_clients: str
    traffic_revenue: str


class KpiEvolutionData(BaseModel):
    monthly: list[MonthlyKpiPoint]
    avg_revenue_per_client: float
    thresholds: dict[str, float]
    product_details: list[dict]
    actual_total_revenue: float | None = None
