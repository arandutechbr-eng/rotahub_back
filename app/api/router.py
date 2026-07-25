from fastapi import APIRouter

from app.api.v1 import auth, freight, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(freight.router)


def register_api_routes(application, prefix: str) -> None:
    """Registra rotas v1 diretamente no app (evita _IncludedRouter aninhado)."""
    application.include_router(health.router, prefix=prefix)
    application.include_router(auth.router, prefix=prefix)
    application.include_router(freight.router, prefix=prefix)
