import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import register_api_routes
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.exceptions import RotaHubError
from app.repositories.toll_plaza import TollPlazaRepository
from app.repositories.user import UserRepository
from app.services.auth import AuthService
from app.services.toll_plaza import TollPlazaService

logger = logging.getLogger(__name__)


def seed_admin_user() -> None:
    """Cria o admin inicial. Falhas não devem impedir o start da API."""
    if SessionLocal is None:
        return

    try:
        with SessionLocal() as session:
            service = AuthService(UserRepository(session))
            created = service.ensure_admin_seed()
            if created is not None:
                session.commit()
                logger.info("Admin inicial criado: %s", created.email)
    except Exception:
        logger.warning(
            "Seed do admin não executado. Rode 'alembic upgrade head' para criar as tabelas.",
            exc_info=True,
        )


def seed_toll_plazas() -> None:
    """Popula praças iniciais a partir do JSON se a tabela estiver vazia."""
    if SessionLocal is None:
        return

    try:
        with SessionLocal() as session:
            service = TollPlazaService(TollPlazaRepository(session))
            created = service.ensure_seed_from_json()
            if created:
                session.commit()
                logger.info("Seed de pedágios: %s praças inseridas.", created)
    except Exception:
        logger.warning(
            "Seed de pedágios não executado. Rode 'alembic upgrade head' para criar as tabelas.",
            exc_info=True,
        )


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    seed_admin_user()
    seed_toll_plazas()
    yield


def register_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(RotaHubError)
    def handle_domain_error(_: Request, exc: RotaHubError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        description="Gestão Inteligente de Rotas e Logística.",
        version="0.3.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(application)
    register_api_routes(application, settings.api_prefix)

    @application.get("/")
    def root() -> dict[str, str]:
        return {
            "message": f"{settings.app_name} API",
            "slogan": "Gestão Inteligente de Rotas e Logística.",
            "docs": "/docs",
        }

    return application


app = create_app()
