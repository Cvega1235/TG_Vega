from datetime import datetime, timezone

from sqlalchemy import (
    String, Integer, Text, Numeric, DateTime, ForeignKey, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.security.encryption import EncryptedString


class Restaurant(Base):
    __tablename__ = "restaurants"
    __table_args__ = (
        CheckConstraint(
            "status IN ('nuevo', 'contactado', 'interesado', 'cliente', 'no_interesado')",
            name="ck_restaurants_status",
        ),
        CheckConstraint("rating >= 0 AND rating <= 5", name="ck_restaurants_rating"),
        Index("ix_restaurants_fuente", "fuente"),
        Index("ix_restaurants_zona", "zona"),
        Index("ix_restaurants_status", "status"),
        Index("ix_restaurants_rating", "rating"),
        Index("ix_restaurants_nombre_fuente", "nombre", "fuente"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fuente: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    nombre: Mapped[str] = mapped_column(String(500), nullable=False)
    direccion: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    telefono: Mapped[str | None] = mapped_column(EncryptedString, nullable=True)
    rating: Mapped[float | None] = mapped_column(Numeric(2, 1), nullable=True)
    num_resenas: Mapped[int | None] = mapped_column(Integer, nullable=True, default=0)
    latitud: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitud: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    precio: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tipo_cocina: Mapped[str | None] = mapped_column(Text, nullable=True)
    categoria: Mapped[str | None] = mapped_column(String(255), nullable=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    servicios: Mapped[str | None] = mapped_column(Text, nullable=True)
    zona: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="nuevo"
    )
    scraped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Sitio web propio del restaurante (extraído de Google Maps)
    website_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Texto extraído del sitio web propio mediante scraping
    website_texto: Mapped[str | None] = mapped_column(Text, nullable=True)
    website_scrapeado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Análisis de menú / productos
    menu_texto_ocr: Mapped[str | None] = mapped_column(Text, nullable=True)
    tiene_embutidos: Mapped[bool | None] = mapped_column(
        nullable=True, default=None
    )
    productos_detectados: Mapped[str | None] = mapped_column(Text, nullable=True)
    menu_analizado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    notes: Mapped[list["RestaurantNote"]] = relationship(
        back_populates="restaurant", cascade="all, delete-orphan"
    )
    status_changes: Mapped[list["RestaurantStatusChange"]] = relationship(
        back_populates="restaurant", cascade="all, delete-orphan"
    )
    score: Mapped["RestaurantScore | None"] = relationship(
        back_populates="restaurant", uselist=False, cascade="all, delete-orphan"
    )
    ml_score: Mapped["RestaurantMLScore | None"] = relationship(
        back_populates="restaurant", uselist=False, cascade="all, delete-orphan"
    )


class RestaurantNote(Base):
    __tablename__ = "restaurant_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    restaurant: Mapped["Restaurant"] = relationship(back_populates="notes")
    user = relationship("User", back_populates="notes")


class RestaurantStatusChange(Base):
    __tablename__ = "restaurant_status_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    old_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    restaurant: Mapped["Restaurant"] = relationship(back_populates="status_changes")
    user = relationship("User", back_populates="status_changes")


class RestaurantScore(Base):
    __tablename__ = "restaurant_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    total_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    cuisine_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    rating_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    reviews_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    zone_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    price_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    completeness_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    restaurant: Mapped["Restaurant"] = relationship(back_populates="score")


class RestaurantMLScore(Base):
    """Score de ML: clustering K-means + similitud al ICP."""

    __tablename__ = "restaurant_ml_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("restaurants.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    cluster_id: Mapped[int] = mapped_column(Integer, nullable=False)
    cluster_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    icp_similarity: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    cluster_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    composite_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    conversion_probability: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    restaurant: Mapped["Restaurant"] = relationship(back_populates="ml_score")


class MLRunMetadata(Base):
    """Metadata de cada ejecución del pipeline de ML."""

    __tablename__ = "ml_run_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    optimal_k: Mapped[int] = mapped_column(Integer, nullable=False)
    silhouette_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    davies_bouldin_index: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    calinski_harabasz_index: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    total_restaurants_scored: Mapped[int] = mapped_column(Integer, nullable=False)
    icp_clients_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # Métricas del clasificador supervisado (nullable: se rellenan solo si hay ≥2 clientes)
    cls_precision: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    cls_recall: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    cls_f1: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    cls_auc_roc: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    cls_cv_f1_mean: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    cls_cv_f1_std: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    cls_support_positive: Mapped[int | None] = mapped_column(Integer, nullable=True)
    run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ScrapingImport(Base):
    __tablename__ = "scraping_imports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_file: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    records_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    records_imported: Mapped[int | None] = mapped_column(Integer, nullable=True)
    records_skipped: Mapped[int | None] = mapped_column(Integer, nullable=True)
    imported_by: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
