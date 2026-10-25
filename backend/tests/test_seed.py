"""Seeding can be repeated without duplicating the catalog."""

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.seed import seed_database
from app.models.spread import TarotSpread, TarotSpreadPosition
from app.models.tarot_card import TarotCard
from app.models.tarot_meaning import TarotMeaning

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_seed_is_idempotent(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        first = await seed_database(session)
        await session.commit()
    async with session_factory() as session:
        second = await seed_database(session)
        await session.commit()
        cards = await session.scalar(select(func.count()).select_from(TarotCard))
        meanings = await session.scalar(select(func.count()).select_from(TarotMeaning))
        spreads = await session.scalar(select(func.count()).select_from(TarotSpread))
        positions = await session.scalar(
            select(func.count()).select_from(TarotSpreadPosition)
        )
        fool = (
            await session.execute(select(TarotCard).where(TarotCard.name == "The Fool"))
        ).scalar_one()
    assert first == second
    assert cards == 78
    assert meanings == 156
    assert spreads == 4
    assert positions == 19
    assert fool.canonical_number == 0
    assert fool.arcana_type == "major"
    assert fool.suit is None
