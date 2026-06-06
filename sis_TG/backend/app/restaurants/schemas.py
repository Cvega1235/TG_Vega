from datetime import datetime
from pydantic import BaseModel


class RestaurantResponse(BaseModel):
    id: int
    fuente: str
    url: str | None = None
    nombre: str
    direccion: str | None = None
    telefono: str | None = None
    rating: float | None = None
    num_resenas: int | None = None
    latitud: float | None = None
    longitud: float | None = None
    precio: str | None = None
    tipo_cocina: str | None = None
    categoria: str | None = None
    descripcion: str | None = None
    servicios: str | None = None
    zona: str | None = None
    status: str
    monthly_revenue: float | None = None
    scraped_at: datetime | None = None
    tiene_embutidos: bool | None = None
    productos_detectados: str | None = None
    menu_analizado_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MLScoreCompact(BaseModel):
    """Score ML compacto para inclusión en la respuesta de restaurante."""

    cluster_id: int
    icp_similarity: float
    composite_score: float

    model_config = {"from_attributes": True}


class RestaurantWithScore(RestaurantResponse):
    score: "ScoreResponse | None" = None
    ml_score: "MLScoreCompact | None" = None


class RestaurantUpdate(BaseModel):
    direccion: str | None = None
    telefono: str | None = None
    zona: str | None = None
    tipo_cocina: str | None = None
    precio: str | None = None
    categoria: str | None = None
    descripcion: str | None = None


class StatusUpdate(BaseModel):
    status: str
    monthly_revenue: float | None = None


class RevenueUpdate(BaseModel):
    monthly_revenue: float


class NoteCreate(BaseModel):
    content: str


class NoteResponse(BaseModel):
    id: int
    restaurant_id: int
    user_id: str
    user_name: str | None = None
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class StatusChangeResponse(BaseModel):
    id: int
    old_status: str | None = None
    new_status: str
    user_name: str | None = None
    changed_at: datetime

    model_config = {"from_attributes": True}


class ScoreResponse(BaseModel):
    total_score: float
    cuisine_score: float | None = None
    rating_score: float | None = None
    reviews_score: float | None = None
    zone_score: float | None = None
    price_score: float | None = None
    completeness_score: float | None = None
    calculated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedRestaurants(BaseModel):
    items: list[RestaurantWithScore]
    total: int
    page: int
    per_page: int
    pages: int
