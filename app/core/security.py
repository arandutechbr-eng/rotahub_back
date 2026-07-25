import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
import jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(
    *,
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(*, user_id: UUID, role: str) -> str:
    return create_token(
        subject=str(user_id),
        token_type="access",
        expires_delta=settings.access_token_expires,
        extra_claims={"role": role},
    )


def create_refresh_token(*, user_id: UUID) -> str:
    return create_token(
        subject=str(user_id),
        token_type="refresh",
        expires_delta=settings.refresh_token_expires,
    )


def decode_token(token: str, *, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Token inválido ou expirado.") from exc

    if payload.get("type") != expected_type:
        raise UnauthorizedError("Tipo de token inválido.")
    if not payload.get("sub"):
        raise UnauthorizedError("Token sem sujeito.")
    return payload


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_token_hash(token: str, token_hash: str | None) -> bool:
    if not token_hash:
        return False
    # Compatível com hashes bcrypt antigos (antes da troca para SHA-256).
    if token_hash.startswith("$2"):
        try:
            return bcrypt.checkpw(token.encode("utf-8"), token_hash.encode("utf-8"))
        except ValueError:
            return False
    return hmac.compare_digest(hash_token(token), token_hash)
