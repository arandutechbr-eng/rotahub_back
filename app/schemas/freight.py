from enum import Enum

from pydantic import BaseModel, Field


class VehicleType(str, Enum):
    TRUCK = "caminhao"
    CAR = "carro"
    VAN = "van"
    MOTORCYCLE = "moto"


class RoutePreference(str, Enum):
    EFFICIENT = "eficiente"
    SHORT = "curta"
    AVOID_TOLLS = "evitar_pedagios"


class FreightSimulateRequest(BaseModel):
    origin: str = Field(min_length=3, max_length=255)
    destination: str = Field(min_length=3, max_length=255)
    vehicle_type: VehicleType = VehicleType.TRUCK
    axles: int = Field(default=2, ge=2, le=12)
    consumption_km_l: float = Field(default=0, ge=0, le=50)
    fuel_price: float = Field(default=0, ge=0, le=100)
    round_trip: bool = False
    route_preference: RoutePreference = RoutePreference.EFFICIENT


class GeoPoint(BaseModel):
    label: str
    latitude: float
    longitude: float


class FreightSimulateResponse(BaseModel):
    origin: GeoPoint
    destination: GeoPoint
    distance_km: float
    duration_minutes: float
    estimated_fuel_cost: float
    estimated_freight_value: float
    currency: str = "BRL"
    route_preference: RoutePreference
    vehicle_type: VehicleType
    axles: int
    round_trip: bool
    geometry: list[list[float]]
    notes: list[str] = Field(default_factory=list)
