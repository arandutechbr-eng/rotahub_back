from app.repositories.base import BaseRepository
from app.models.toll_plaza import TollPlaza


class TollPlazaRepository(BaseRepository[TollPlaza]):
    model = TollPlaza
    search_fields = ("code", "name", "road", "concessionaire")
    default_order_by = "name"

    def list_active(self) -> list[TollPlaza]:
        return list(
            self.list(
                skip=0,
                limit=10_000,
                order_by="name",
                descending=False,
                filters={"is_active": True},
            )
        )

    def get_by_code(self, code: str) -> TollPlaza | None:
        return self.get_by_field("code", code)
