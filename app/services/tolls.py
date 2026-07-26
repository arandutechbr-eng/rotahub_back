from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from typing import Any

from app.schemas.freight import TollPlazaHit, VehicleType

# Distância máxima (km) entre a praça e a linha da rota para considerá-la no trajeto.
_MATCH_THRESHOLD_KM = 1.5

# Multiplicador de eixos por tipo de veículo (praças cobram por eixo).
_MOTORCYCLE_FACTOR = 0.5


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * r * asin(sqrt(a))


class TollService:
    """Detecta praças de pedágio ao longo da rota e calcula a tarifa por eixo.

    As praças vêm do banco (CRUD admin). Passe a lista via construtor.
    """

    def __init__(self, plazas: list[dict[str, Any]] | None = None) -> None:
        self._plazas = plazas or []

    def _passage_cost(self, tariff_per_axle: float, vehicle_type: VehicleType, axles: int) -> float:
        if vehicle_type == VehicleType.MOTORCYCLE:
            return tariff_per_axle * _MOTORCYCLE_FACTOR
        if vehicle_type == VehicleType.TRUCK:
            return tariff_per_axle * max(axles, 2)
        return tariff_per_axle * 2

    def detect(
        self,
        geometry: list[list[float]],
        vehicle_type: VehicleType,
        axles: int,
        *,
        passes: int = 1,
    ) -> list[TollPlazaHit]:
        if not self._plazas or not geometry:
            return []

        found: list[TollPlazaHit] = []
        for plaza in self._plazas:
            try:
                lat = float(plaza["latitude"])
                lon = float(plaza["longitude"])
                tariff = float(plaza["tariff_per_axle"])
            except (KeyError, TypeError, ValueError):
                continue

            on_route = any(
                _haversine_km(lat, lon, point[0], point[1]) <= _MATCH_THRESHOLD_KM
                for point in geometry
            )
            if not on_route:
                continue

            cost = self._passage_cost(tariff, vehicle_type, axles) * passes
            found.append(
                TollPlazaHit(
                    id=str(plaza.get("id", plaza.get("code", plaza.get("name", "praca")))),
                    name=str(plaza.get("name", "Praça de Pedágio")),
                    road=str(plaza.get("road", "")),
                    concessionaire=str(plaza.get("concessionaire", "")),
                    latitude=lat,
                    longitude=lon,
                    cost=round(cost, 2),
                )
            )

        return found
