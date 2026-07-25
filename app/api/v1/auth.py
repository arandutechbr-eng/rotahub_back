from fastapi import APIRouter

from app.dependencies.auth import AuthServiceDep, CurrentUser
from app.schemas.auth import AuthResponse, LoginRequest, RefreshRequest, UserResponse
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, service: AuthServiceDep) -> AuthResponse:
    return service.login(payload.email, payload.password)


@router.post("/refresh", response_model=AuthResponse)
def refresh(payload: RefreshRequest, service: AuthServiceDep) -> AuthResponse:
    return service.refresh(payload.refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(current_user: CurrentUser, service: AuthServiceDep) -> MessageResponse:
    service.logout(current_user.id)
    return MessageResponse(message="Logout realizado com sucesso.")


@router.get("/me", response_model=UserResponse)
def me(current_user: CurrentUser, service: AuthServiceDep) -> UserResponse:
    return service.get_profile(current_user.id)
