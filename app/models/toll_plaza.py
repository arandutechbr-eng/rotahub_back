from typing import Optional

from sqlalchemy import Boolean, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TollPlaza(BaseModel):
    """Praça de pedágio cadastrada (admin). Usada na detecção ao longo da rota."""

    __tablename__ = "toll_plazas"

    code: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    road: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    concessionaire: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    tariff_per_axle: Mapped[float] = mapped_column(Float, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
