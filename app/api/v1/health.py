from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    app: str
    env: str
    database: Literal["ok", "error", "not_configured"]


def _check_database() -> Literal["ok", "error", "not_configured"]:
    if SessionLocal is None:
        return "not_configured"

    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "error"


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    database = _check_database()
    return HealthResponse(
        status="ok" if database == "ok" else "degraded",
        app=settings.app_name,
        env=settings.app_env,
        database=database,
    )
