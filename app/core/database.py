from collections.abc import Generator
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


def _engine_options() -> dict[str, Any]:
    options: dict[str, Any] = {
        "echo": settings.db_echo,
        "pool_pre_ping": True,
        "future": True,
    }

    if settings.uses_transaction_pooler:
        # PgBouncer em modo transaction não suporta prepared statements nem pool no cliente.
        options["poolclass"] = NullPool
        options["connect_args"] = {"prepare_threshold": None}
    else:
        options["pool_size"] = settings.db_pool_size
        options["max_overflow"] = settings.db_max_overflow

    return options


def create_database_engine(url: str | None = None) -> Engine:
    target = url or settings.database_url
    if not target:
        raise RuntimeError("DATABASE_URL não configurada. Defina no arquivo .env.")
    return create_engine(target, **_engine_options())


engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None

if settings.has_database:
    engine = create_database_engine()
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    if SessionLocal is None:
        raise RuntimeError("Banco de dados não configurado. Defina DATABASE_URL no .env.")

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
