from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User
    search_fields = ("name", "email")
    default_order_by = "created_at"

    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        return self.session.execute(statement).scalar_one_or_none()

    def get_active_by_id(self, user_id: UUID) -> User | None:
        user = self.get_by_id(user_id)
        if user is None or not user.is_active:
            return None
        return user

    def count_all(self) -> int:
        return self.count()
