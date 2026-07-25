from uuid import UUID

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
    verify_token_hash,
)
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.auth import AuthResponse, TokenResponse, UserResponse
from app.services.base import BaseService


class AuthService(BaseService[User, UserRepository]):
    not_found_message = "Usuário não encontrado."

    def ensure_admin_seed(self) -> User | None:
        if self.repository.count_all() > 0:
            return None

        return self.repository.create(
            {
                "name": settings.admin_name,
                "email": settings.admin_email.lower(),
                "password_hash": hash_password(settings.admin_password),
                "role": UserRole.ADMIN,
                "is_active": True,
            }
        )

    def login(self, email: str, password: str) -> AuthResponse:
        user = self.repository.get_by_email(email.lower())
        if user is None or not user.is_active:
            raise UnauthorizedError("E-mail ou senha inválidos.")
        if not verify_password(password, user.password_hash):
            raise UnauthorizedError("E-mail ou senha inválidos.")

        tokens = self._issue_tokens(user)
        return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)

    def refresh(self, refresh_token: str) -> AuthResponse:
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = UUID(str(payload["sub"]))
        user = self.repository.get_active_by_id(user_id)
        if user is None:
            raise UnauthorizedError("Sessão inválida.")
        if not verify_token_hash(refresh_token, user.refresh_token_hash):
            raise UnauthorizedError("Refresh token inválido.")

        tokens = self._issue_tokens(user)
        return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)

    def logout(self, user_id: UUID) -> None:
        user = self.get(user_id)
        self.repository.update(user, {"refresh_token_hash": None})

    def get_profile(self, user_id: UUID) -> UserResponse:
        user = self.get(user_id)
        return UserResponse.model_validate(user)

    def _issue_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(user_id=user.id, role=user.role.value)
        refresh_token = create_refresh_token(user_id=user.id)
        self.repository.update(user, {"refresh_token_hash": hash_token(refresh_token)})
        return TokenResponse(access_token=access_token, refresh_token=refresh_token)
