from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.schemas.freight import GeoPoint, RoutePreference


class RoutingService:
    """Geocoding (Nominatim) + roteirização (OSRM). Extensível para OpenRouteService."""

    def __init__(self) -> None:
        self._headers = {
            "User-Agent": settings.routing_user_agent,
            "Accept": "application/json",
        }

    async def geocode(self, query: str) -> GeoPoint:
        params = {
            "q": query,
            "format": "json",
            "limit": 1,
            "countrycodes": "br",
        }
        try:
            async with httpx.AsyncClient(timeout=20.0, headers=self._headers) as client:
                response = await client.get(f"{settings.nominatim_base_url}/search", params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise ValidationError("Falha ao consultar o serviço de geocoding.") from exc

        if not payload:
            raise ValidationError(f"Não foi possível localizar: {query}")

        item = payload[0]
        return GeoPoint(
            label=item.get("display_name", query),
            latitude=float(item["lat"]),
            longitude=float(item["lon"]),
        )

    async def route(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        preference: RoutePreference,
    ) -> dict[str, Any]:
        coordinates = f"{origin.longitude},{origin.latitude};{destination.longitude},{destination.latitude}"
        params: dict[str, str] = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false",
        }
        if preference == RoutePreference.SHORT:
            params["alternatives"] = "true"

        url = f"{settings.osrm_base_url}/route/v1/driving/{coordinates}"
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=self._headers) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPError as exc:
            raise ValidationError("Falha ao consultar o serviço de roteirização.") from exc

        if payload.get("code") != "Ok" or not payload.get("routes"):
            raise ValidationError("Não foi possível calcular a rota entre origem e destino.")

        routes = payload["routes"]
        selected = (
            min(routes, key=lambda item: item["distance"])
            if preference == RoutePreference.SHORT
            else routes[0]
        )
        geometry = selected["geometry"]["coordinates"]

        return {
            "distance_m": float(selected["distance"]),
            "duration_s": float(selected["duration"]),
            "geometry": [[float(lat), float(lon)] for lon, lat in geometry],
        }
