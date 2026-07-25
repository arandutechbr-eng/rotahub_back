from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel as PydanticBaseModel
from pydantic import ConfigDict, Field

ItemType = TypeVar("ItemType")


class PaginationParams(PydanticBaseModel):
    page: int = Field(default=1, ge=1, description="Página atual")
    page_size: int = Field(default=20, ge=1, le=100, description="Itens por página")
    search: str | None = Field(default=None, description="Termo de pesquisa")
    order_by: str | None = Field(default=None, description="Campo de ordenação")
    descending: bool = Field(default=True, description="Ordenação decrescente")

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.page_size


class Page(PydanticBaseModel, Generic[ItemType]):
    model_config = ConfigDict(from_attributes=True)

    items: list[ItemType]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        *,
        items: list[ItemType],
        total: int,
        page: int,
        page_size: int,
    ) -> "Page[ItemType]":
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if page_size else 0,
        )


class MessageResponse(PydanticBaseModel):
    message: str
