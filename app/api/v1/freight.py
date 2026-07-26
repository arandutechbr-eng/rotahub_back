from fastapi import APIRouter

from app.dependencies.auth import CurrentUser
from app.dependencies.database import DbSession
from app.schemas.freight import FreightSimulateRequest, FreightSimulateResponse
from app.services.freight import FreightService

router = APIRouter(prefix="/freight", tags=["Freight"])


@router.post("/simulate", response_model=FreightSimulateResponse)
async def simulate_freight(
    payload: FreightSimulateRequest,
    _: CurrentUser,
    session: DbSession,
) -> FreightSimulateResponse:
    return await FreightService(session=session).simulate(payload)
