"""Pydantic schemas para el módulo de Machine Learning."""

from datetime import datetime

from pydantic import BaseModel


class MLScoreResponse(BaseModel):
    """Score de ML de un restaurante."""

    cluster_id: int
    cluster_label: str | None = None
    icp_similarity: float
    cluster_score: float
    composite_score: float
    conversion_probability: float | None = None
    calculated_at: datetime

    model_config = {"from_attributes": True}


class MLRunResponse(BaseModel):
    """Metadata de una ejecución del pipeline ML."""

    id: int
    optimal_k: int
    silhouette_score: float
    davies_bouldin_index: float
    calinski_harabasz_index: float
    total_restaurants_scored: int
    icp_clients_count: int
    run_at: datetime

    model_config = {"from_attributes": True}


class ClusterProfileResponse(BaseModel):
    """Perfil descriptivo de un cluster."""

    cluster_id: int
    label: str | None = None
    size: int
    avg_rating: float | None = None
    avg_reviews: float | None = None
    dominant_cuisine: str | None = None
    dominant_zone: str | None = None
    dominant_price: str | None = None
    avg_composite_score: float | None = None


class MLRunResultResponse(BaseModel):
    """Resultado completo de una ejecución del pipeline ML."""

    run_metadata: MLRunResponse
    cluster_profiles: list[ClusterProfileResponse]
    message: str


class ValidationReport(BaseModel):
    """Reporte de validación de la última ejecución ML."""

    run_at: datetime
    total_restaurants_scored: int
    icp_clients_count: int
    # Clustering
    silhouette_score: float
    davies_bouldin_index: float
    calinski_harabasz_index: float
    optimal_k: int
    # Clasificador supervisado
    classifier_available: bool
    cls_precision: float | None = None
    cls_recall: float | None = None
    cls_f1: float | None = None
    cls_auc_roc: float | None = None
    cls_cv_f1_mean: float | None = None
    cls_cv_f1_std: float | None = None
    cls_support_positive: int | None = None


class TopProspectResponse(BaseModel):
    """Prospecto con score ML."""

    id: int
    nombre: str
    fuente: str
    zona: str | None = None
    rating: float | None = None
    tipo_cocina: str | None = None
    precio: str | None = None
    cluster_id: int | None = None
    icp_similarity: float | None = None
    composite_score: float | None = None
    total_score: float | None = None

    model_config = {"from_attributes": True}
