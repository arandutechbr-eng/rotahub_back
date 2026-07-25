from typing import Annotated

from fastapi import Depends, Query

from app.schemas.common import PaginationParams


def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="Página atual")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Itens por página")] = 20,
    search: Annotated[str | None, Query(description="Termo de pesquisa")] = None,
    order_by: Annotated[str | None, Query(description="Campo de ordenação")] = None,
    descending: Annotated[bool, Query(description="Ordenação decrescente")] = True,
) -> PaginationParams:
    return PaginationParams(
        page=page,
        page_size=page_size,
        search=search,
        order_by=order_by,
        descending=descending,
    )


Pagination = Annotated[PaginationParams, Depends(get_pagination_params)]
