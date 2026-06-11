from datetime import datetime, timezone

from sqlalchemy import Integer, Numeric, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class KpiSettings(Base):
    __tablename__ = "kpi_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    revenue_green: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    revenue_yellow: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    clients_green: Mapped[int] = mapped_column(Integer, nullable=False)
    clients_yellow: Mapped[int] = mapped_column(Integer, nullable=False)
    new_clients_green: Mapped[int] = mapped_column(Integer, nullable=False)
    new_clients_yellow: Mapped[int] = mapped_column(Integer, nullable=False)
    max_clients: Mapped[int] = mapped_column(Integer, nullable=False, default=72)
    max_kg_day: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False, default=100.0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
