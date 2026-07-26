from sqlalchemy.orm import Session

from app.repositories.toll_plaza import TollPlazaRepository
from app.schemas.freight import (
    FreightSimulateRequest,
    FreightSimulateResponse,
    RoutePreference,
    VehicleType,
)
from app.services.routing import RoutingService
from app.services.toll_plaza import TollPlazaService
from app.services.tolls import TollService

# Tarifa operacional base por km (BRL).
BASE_RATE_PER_KM: dict[VehicleType, float] = {
    VehicleType.TRUCK: 3.80,
    VehicleType.VAN: 2.40,
    VehicleType.CAR: 1.60,
    VehicleType.MOTORCYCLE: 1.10,
}


class FreightService:
    def __init__(
        self,
        session: Session | None = None,
        routing_service: RoutingService | None = None,
        toll_service: TollService | None = None,
    ) -> None:
        self.session = session
        self.routing = routing_service or RoutingService()
        self.tolls = toll_service

    def _resolve_toll_service(self) -> TollService:
        if self.tolls is not None:
            return self.tolls
        if self.session is None:
            return TollService([])
        plazas = TollPlazaService(TollPlazaRepository(self.session)).list_active_for_routing()
        return TollService(plazas)

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

        toll_service = self._resolve_toll_service()
        tolls = toll_service.detect(
            route["geometry"],
            payload.vehicle_type,
            payload.axles,
            passes=multiplier,
        )
        toll_cost = round(sum(item.cost for item in tolls), 2)

        if tolls:
            plazas = "praça" if len(tolls) == 1 else "praças"
            notes.append(f"{len(tolls)} {plazas} de pedágio na rota (tarifa por eixo).")
            if payload.route_preference == RoutePreference.AVOID_TOLLS:
                notes.append(
                    "Preferência 'evitar pedágios' registrada, mas o desvio automático ainda não é aplicado."
                )
        elif payload.route_preference == RoutePreference.AVOID_TOLLS:
            notes.append("Nenhuma praça de pedágio ativa cadastrada na rota.")

        freight_value = round(operational + fuel_cost + toll_cost, 2)
        notes.append("Valores estimados. Pedágios vêm do cadastro admin — confira as tarifas oficiais.")

        return FreightSimulateResponse(
            origin=origin,
            destination=destination,
            distance_km=round(distance_total, 2),
            duration_minutes=round(duration_total, 1),
            estimated_fuel_cost=round(fuel_cost, 2),
            estimated_toll_cost=toll_cost,
            estimated_freight_value=freight_value,
            route_preference=payload.route_preference,
            vehicle_type=payload.vehicle_type,
            axles=payload.axles,
            round_trip=payload.round_trip,
            geometry=route["geometry"],
            tolls=tolls,
            notes=notes,
        )
