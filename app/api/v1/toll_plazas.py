from uuid import UUID

from fastapi import APIRouter

from app.dependencies.auth import AdminUser, CurrentUser
from app.dependencies.database import DbSession
from app.dependencies.pagination import Pagination
from app.repositories.toll_plaza import TollPlazaRepository
from app.schemas.common import MessageResponse, Page
from app.schemas.toll_plaza import TollPlazaCreate, TollPlazaResponse, TollPlazaUpdate
from app.services.toll_plaza import TollPlazaService

router = APIRouter(prefix="/toll-plazas", tags=["Toll Plazas"])


def _service(session: DbSession) -> TollPlazaService:
    return TollPlazaService(TollPlazaRepository(session))


@router.get("", response_model=Page[TollPlazaResponse])
def list_toll_plazas(
    pagination: Pagination,
    _: CurrentUser,
    session: DbSession,
) -> Page[TollPlazaResponse]:
    page = _service(session).list_plazas(pagination)
    return Page.create(
        items=[TollPlazaResponse.model_validate(item) for item in page.items],
        total=page.total,
        page=page.page,
        page_size=page.page_size,
    )


@router.get("/{plaza_id}", response_model=TollPlazaResponse)
def get_toll_plaza(
    plaza_id: UUID,
    _: CurrentUser,
    session: DbSession,
) -> TollPlazaResponse:
    plaza = _service(session).get(plaza_id)
    return TollPlazaResponse.model_validate(plaza)


@router.post("", response_model=TollPlazaResponse, status_code=201)
def create_toll_plaza(
    payload: TollPlazaCreate,
    _: AdminUser,
    session: DbSession,
) -> TollPlazaResponse:
    plaza = _service(session).create_plaza(payload)
    return TollPlazaResponse.model_validate(plaza)


@router.patch("/{plaza_id}", response_model=TollPlazaResponse)
def update_toll_plaza(
    plaza_id: UUID,
    payload: TollPlazaUpdate,
    _: AdminUser,
    session: DbSession,
) -> TollPlazaResponse:
    plaza = _service(session).update_plaza(plaza_id, payload)
    return TollPlazaResponse.model_validate(plaza)


@router.delete("/{plaza_id}", response_model=MessageResponse)
def delete_toll_plaza(
    plaza_id: UUID,
    _: AdminUser,
    session: DbSession,
) -> MessageResponse:
    _service(session).delete_plaza(plaza_id)
    return MessageResponse(message="Praça removida com sucesso.")
