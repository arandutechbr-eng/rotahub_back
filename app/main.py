from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        description="Gestão Inteligente de Rotas e Logística.",
        version="0.1.0",
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
