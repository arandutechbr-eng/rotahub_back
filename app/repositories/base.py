from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Acesso a dados genérico. Subclasses definem `model` e `search_fields`."""

    model: type[ModelType]
    search_fields: tuple[str, ...] = ()
    default_order_by: str = "created_at"

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, entity_id: Any) -> ModelType | None:
        return self.session.get(self.model, entity_id)

    def get_by_field(self, field: str, value: Any) -> ModelType | None:
        statement = select(self.model).where(getattr(self.model, field) == value)
        return self.session.execute(statement).scalar_one_or_none()

    def list(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
        order_by: str | None = None,
        descending: bool = True,
        filters: dict[str, Any] | None = None,
    ) -> Sequence[ModelType]:
        statement = self._apply_filters(select(self.model), search=search, filters=filters)
        statement = self._apply_ordering(statement, order_by=order_by, descending=descending)
        statement = statement.offset(skip).limit(limit)
        return self.session.execute(statement).scalars().all()

    def count(
        self,
        *,
        search: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> int:
        statement = self._apply_filters(
            select(func.count()).select_from(self.model),
            search=search,
            filters=filters,
        )
        return self.session.execute(statement).scalar_one()

    def create(self, data: dict[str, Any]) -> ModelType:
        entity = self.model(**data)
        self.session.add(entity)
        self.session.flush()
        return entity

    def update(self, entity: ModelType, data: dict[str, Any]) -> ModelType:
        for field, value in data.items():
            setattr(entity, field, value)
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity: ModelType) -> None:
        self.session.delete(entity)
        self.session.flush()

    def exists_by_field(self, field: str, value: Any, *, exclude_id: Any | None = None) -> bool:
        statement = select(func.count()).select_from(self.model).where(getattr(self.model, field) == value)
        if exclude_id is not None:
            statement = statement.where(self.model.id != exclude_id)
        return self.session.execute(statement).scalar_one() > 0

    def _apply_filters(
        self,
        statement: Select[Any],
        *,
        search: str | None,
        filters: dict[str, Any] | None,
    ) -> Select[Any]:
        if search and self.search_fields:
            pattern = f"%{search.strip()}%"
            conditions = [getattr(self.model, field).ilike(pattern) for field in self.search_fields]
            statement = statement.where(or_(*conditions))

        for field, value in (filters or {}).items():
            if value is None or not hasattr(self.model, field):
                continue
            statement = statement.where(getattr(self.model, field) == value)

        return statement

    def _apply_ordering(
        self,
        statement: Select[Any],
        *,
        order_by: str | None,
        descending: bool,
    ) -> Select[Any]:
        field_name = order_by if order_by and hasattr(self.model, order_by) else self.default_order_by
        column = getattr(self.model, field_name)
        return statement.order_by(column.desc() if descending else column.asc())
