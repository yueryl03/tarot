"""Catalog queries."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tarot_card import TarotCard
from app.models.tarot_meaning import TarotMeaning  # noqa: F401  (registers the relationship)


class CardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_cards(self) -> list[TarotCard]:
        statement = (
            select(TarotCard)
            .options(selectinload(TarotCard.meanings))
            .order_by(TarotCard.canonical_number)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_ids(self) -> list[int]:
        statement = select(TarotCard.id).order_by(TarotCard.canonical_number)
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_by_ids(self, card_ids: list[int]) -> dict[int, TarotCard]:
        if not card_ids:
            return {}
        statement = (
            select(TarotCard)
            .where(TarotCard.id.in_(card_ids))
            .options(selectinload(TarotCard.meanings))
        )
        result = await self.session.execute(statement)
        return {card.id: card for card in result.scalars().unique().all()}
