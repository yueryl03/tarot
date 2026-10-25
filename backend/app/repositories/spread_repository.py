"""Spread queries."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.spread import TarotSpread


class SpreadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> list[TarotSpread]:
        statement = (
            select(TarotSpread)
            .options(selectinload(TarotSpread.positions))
            .order_by(TarotSpread.card_count, TarotSpread.slug)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().unique().all())

    async def get_by_slug(self, slug: str) -> TarotSpread | None:
        statement = (
            select(TarotSpread)
            .where(TarotSpread.slug == slug)
            .options(selectinload(TarotSpread.positions))
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id(self, spread_id: int) -> TarotSpread | None:
        statement = (
            select(TarotSpread)
            .where(TarotSpread.id == spread_id)
            .options(selectinload(TarotSpread.positions))
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
