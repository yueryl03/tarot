"""Load spreads. Draw limits come from the stored card_count."""

from app.domain.errors import TarotError
from app.models.spread import TarotSpread
from app.repositories.spread_repository import SpreadRepository
from sqlalchemy.ext.asyncio import AsyncSession


class SpreadService:
    def __init__(self, session: AsyncSession) -> None:
        self.repository = SpreadRepository(session)

    async def list_spreads(self) -> list[TarotSpread]:
        return await self.repository.list_all()

    async def require_by_slug(self, slug: str) -> TarotSpread:
        spread = await self.repository.get_by_slug(slug)
        if spread is None:
            raise TarotError(
                "Spread not found.",
                code="spread_not_found",
                details={"spread_slug": slug},
            )
        self.ensure_positions(spread)
        return spread

    async def require_by_id(self, spread_id: int) -> TarotSpread:
        spread = await self.repository.get_by_id(spread_id)
        if spread is None:
            raise TarotError(
                "Spread not found.",
                code="spread_not_found",
                details={"spread_id": spread_id},
            )
        self.ensure_positions(spread)
        return spread

    @staticmethod
    def ensure_positions(spread: TarotSpread) -> None:
        indexes = {position.position_index for position in spread.positions}
        if indexes != set(range(spread.card_count)):
            raise TarotError(
                "Spread positions do not match the spread's card count.",
                code="spread_integrity",
                details={"spread_id": spread.id, "slug": spread.slug},
            )
