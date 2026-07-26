from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TollPlazaCreate(BaseModel):
    code: str = Field(min_length=2, max_length=80)
    name: str = Field(min_length=2, max_length=160)
    road: str = Field(default="", max_length=160)
    concessionaire: str = Field(default="", max_length=120)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    tariff_per_axle: float = Field(gt=0, le=500)
    is_active: bool = True
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        code = value.strip().lower().replace(" ", "-")
        if not code:
            raise ValueError("Informe um código para a praça.")
        return code

    @field_validator("name", "road", "concessionaire")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class TollPlazaUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=2, max_length=80)
    name: str | None = Field(default=None, min_length=2, max_length=160)
    road: str | None = Field(default=None, max_length=160)
    concessionaire: str | None = Field(default=None, max_length=120)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    tariff_per_axle: float | None = Field(default=None, gt=0, le=500)
    is_active: bool | None = None
    notes: str | None = Field(default=None, max_length=500)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str | None) -> str | None:
        if value is None:
            return value
        code = value.strip().lower().replace(" ", "-")
        if not code:
            raise ValueError("Informe um código para a praça.")
        return code

    @field_validator("name", "road", "concessionaire")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else value


class TollPlazaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    road: str
    concessionaire: str
    latitude: float
    longitude: float
    tariff_per_axle: float
    is_active: bool
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
