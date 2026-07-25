from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.dependencies.database import DbSession
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.services.auth import AuthService

bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(session: DbSession) -> AuthService:
    return AuthService(UserRepository(session))


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


def get_current_user(
    session: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("Autenticação necessária.")

    payload = decode_token(credentials.credentials, expected_type="access")
    user_id = UUID(str(payload["sub"]))
    user = UserRepository(session).get_active_by_id(user_id)
    if user is None:
        raise UnauthorizedError("Usuário inválido ou inativo.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    allowed = set(roles)

    def dependency(user: CurrentUser) -> User:
        if user.role not in allowed:
            raise ForbiddenError("Permissão insuficiente para esta ação.")
        return user

    return dependency


AdminUser = Annotated[User, Depends(require_roles(UserRole.ADMIN))]
