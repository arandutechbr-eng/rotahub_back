from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import RotaHubError


def register_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(RotaHubError)
    def handle_domain_error(_: Request, exc: RotaHubError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        description="Gestão Inteligente de Rotas e Logística.",
        version="0.2.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(application)
    application.include_router(api_router, prefix=settings.api_prefix)

    @application.get("/")
    def root() -> dict[str, str]:
        return {
            "message": f"{settings.app_name} API",
            "slogan": "Gestão Inteligente de Rotas e Logística.",
            "docs": "/docs",
        }

    return application


app = create_app()
