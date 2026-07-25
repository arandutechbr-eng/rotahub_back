from typing import Any, Generic, TypeVar

from app.core.exceptions import NotFoundError
from app.models.base import BaseModel
from app.repositories.base import BaseRepository
from app.schemas.common import Page, PaginationParams

ModelType = TypeVar("ModelType", bound=BaseModel)
RepositoryType = TypeVar("RepositoryType", bound=BaseRepository[Any])


class BaseService(Generic[ModelType, RepositoryType]):
    """Regras de negócio genéricas de CRUD. Toda lógica vive aqui, nunca nas rotas."""

    not_found_message = "Registro não encontrado."

    def __init__(self, repository: RepositoryType) -> None:
        self.repository = repository

    def get(self, entity_id: Any) -> ModelType:
        entity = self.repository.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError(self.not_found_message)
        return entity

    def list(
        self,
        pagination: PaginationParams,
        *,
        filters: dict[str, Any] | None = None,
    ) -> Page[ModelType]:
        items = self.repository.list(
            skip=pagination.skip,
            limit=pagination.page_size,
            search=pagination.search,
            order_by=pagination.order_by,
            descending=pagination.descending,
            filters=filters,
        )
        total = self.repository.count(search=pagination.search, filters=filters)
        return Page.create(
            items=list(items),
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )

    def create(self, data: dict[str, Any]) -> ModelType:
        return self.repository.create(data)

    def update(self, entity_id: Any, data: dict[str, Any]) -> ModelType:
        entity = self.get(entity_id)
        return self.repository.update(entity, data)

    def delete(self, entity_id: Any) -> None:
        entity = self.get(entity_id)
        self.repository.delete(entity)
