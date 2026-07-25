from app.schemas.freight import (
    FreightSimulateRequest,
    FreightSimulateResponse,
    VehicleType,
)
from app.services.routing import RoutingService

# Tarifa operacional base por km (BRL) — estrutura preparada para pedágio/imposto futuros.
BASE_RATE_PER_KM: dict[VehicleType, float] = {
    VehicleType.TRUCK: 3.80,
    VehicleType.VAN: 2.40,
    VehicleType.CAR: 1.60,
    VehicleType.MOTORCYCLE: 1.10,
}


class FreightService:
    def __init__(self, routing_service: RoutingService | None = None) -> None:
        self.routing = routing_service or RoutingService()

    async def simulate(self, payload: FreightSimulateRequest) -> FreightSimulateResponse:
        origin = await self.routing.geocode(payload.origin)
        destination = await self.routing.geocode(payload.destination)
        route = await self.routing.route(origin, destination, payload.route_preference)

        distance_km = route["distance_m"] / 1000
        duration_minutes = route["duration_s"] / 60
        multiplier = 2 if payload.round_trip else 1

        distance_total = distance_km * multiplier
        duration_total = duration_minutes * multiplier

        fuel_cost = 0.0
        notes: list[str] = []
        if payload.consumption_km_l > 0 and payload.fuel_price > 0:
            fuel_cost = (distance_total / payload.consumption_km_l) * payload.fuel_price
        else:
            notes.append("Informe consumo e preço do combustível para estimar o custo de combustível.")

        base_rate = BASE_RATE_PER_KM[payload.vehicle_type]
        axle_factor = 1.0
        if payload.vehicle_type == VehicleType.TRUCK:
            axle_factor = 1.0 + max(payload.axles - 2, 0) * 0.08

        operational = distance_total * base_rate * axle_factor
        freight_value = round(operational + fuel_cost, 2)

        if payload.route_preference.value == "evitar_pedagios":
            notes.append("Evitar pedágios será aplicado quando a integração de pedágios estiver disponível.")

        notes.append("Valores estimados. Pedágios, impostos e margem poderão ser incluídos nas próximas versões.")

        return FreightSimulateResponse(
            origin=origin,
            destination=destination,
            distance_km=round(distance_total, 2),
            duration_minutes=round(duration_total, 1),
            estimated_fuel_cost=round(fuel_cost, 2),
            estimated_freight_value=freight_value,
            route_preference=payload.route_preference,
            vehicle_type=payload.vehicle_type,
            axles=payload.axles,
            round_trip=payload.round_trip,
            geometry=route["geometry"],
            notes=notes,
        )
