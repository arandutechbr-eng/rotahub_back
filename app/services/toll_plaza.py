import json
import logging
from pathlib import Path
from typing import Any
from uuid import UUID

from app.core.exceptions import ConflictError
from app.models.toll_plaza import TollPlaza
from app.repositories.toll_plaza import TollPlazaRepository
from app.schemas.common import Page, PaginationParams
from app.schemas.toll_plaza import TollPlazaCreate, TollPlazaUpdate
from app.services.base import BaseService

logger = logging.getLogger(__name__)

_SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "toll_plazas.json"


class TollPlazaService(BaseService[TollPlaza, TollPlazaRepository]):
    not_found_message = "Praça de pedágio não encontrada."

    def list_plazas(self, pagination: PaginationParams) -> Page[Any]:
        return self.list(pagination)

    def create_plaza(self, payload: TollPlazaCreate) -> TollPlaza:
        if self.repository.exists_by_field("code", payload.code):
            raise ConflictError(f"Já existe uma praça com o código '{payload.code}'.")
        return self.create(payload.model_dump())

    def update_plaza(self, plaza_id: UUID, payload: TollPlazaUpdate) -> TollPlaza:
        data = payload.model_dump(exclude_unset=True)
        if "code" in data and self.repository.exists_by_field("code", data["code"], exclude_id=plaza_id):
            raise ConflictError(f"Já existe uma praça com o código '{data['code']}'.")
        return self.update(plaza_id, data)

    def delete_plaza(self, plaza_id: UUID) -> None:
        self.delete(plaza_id)

    def list_active_for_routing(self) -> list[dict[str, Any]]:
        return [
            {
                "id": str(item.id),
                "code": item.code,
                "name": item.name,
                "road": item.road,
                "concessionaire": item.concessionaire,
                "latitude": item.latitude,
                "longitude": item.longitude,
                "tariff_per_axle": item.tariff_per_axle,
            }
            for item in self.repository.list_active()
        ]

    def ensure_seed_from_json(self) -> int:
        """Insere praças do JSON somente se a tabela estiver vazia."""
        if self.repository.count() > 0:
            return 0

        try:
            with _SEED_FILE.open(encoding="utf-8") as file:
                raw = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning("Seed de pedágios ignorado: arquivo inválido ou ausente.")
            return 0

        if not isinstance(raw, list):
            return 0

        created = 0
        for item in raw:
            try:
                payload = TollPlazaCreate(
                    code=str(item["id"]),
                    name=str(item["name"]),
                    road=str(item.get("road", "")),
                    concessionaire=str(item.get("concessionaire", "")),
                    latitude=float(item["latitude"]),
                    longitude=float(item["longitude"]),
                    tariff_per_axle=float(item["tariff_per_axle"]),
                    is_active=True,
                )
            except (KeyError, TypeError, ValueError):
                continue
            self.create(payload.model_dump())
            created += 1
        return created
