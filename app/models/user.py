import enum
from typing import Optional

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    ADMIN = "administrador"
    OPERATOR = "operador"


class User(BaseModel):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=UserRole.OPERATOR,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    refresh_token_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
