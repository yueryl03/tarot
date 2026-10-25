"""Idempotent seed for the 78 cards, their meanings, and the built-in spreads."""

import asyncio
from dataclasses import dataclass

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import configure_logging
from app.core.config import get_settings
from app.db.card_catalog import all_cards, meanings_for, validate_card_catalog
from app.db.session import dispose_engine, get_session_factory
from app.db.spread_catalog import all_spreads, validate_spread_catalog
from app.models.spread import TarotSpread, TarotSpreadPosition
from app.models.tarot_card import TarotCard
from app.models.tarot_meaning import TarotMeaning


@dataclass(frozen=True, slots=True)
class SeedSummary:
    cards: int
    meanings: int
    spreads: int
    positions: int

    def __str__(self) -> str:
        return (
            f"Seeded {self.cards} cards, {self.meanings} meanings, "
            f"{self.spreads} spreads, {self.positions} positions."
        )


async def seed_database(session: AsyncSession) -> SeedSummary:
    """Insert or update catalog rows. Safe to run more than once.

    Cards are matched on ``canonical_number`` and are never deleted, so an
    existing reading keeps a stable foreign key. Meanings and spread positions
    are replaced in place from the current catalog.
    """

    cards = validate_card_catalog()
    spreads = validate_spread_catalog()
    await _upsert_cards(session, cards)
    await _upsert_meanings(session, cards)
    position_count = await _upsert_spreads(session, spreads)
    return SeedSummary(
        cards=len(cards),
        meanings=len(cards) * 2,
        spreads=len(spreads),
        positions=position_count,
    )


async def _upsert_cards(session: AsyncSession, cards: tuple) -> None:
    rows = [
        {
            "id": card.id,
            "name": card.name,
            "arcana_type": card.arcana_type,
            "suit": card.suit,
            "rank": card.rank,
            "canonical_number": card.canonical_number,
            "description": card.description,
            "image_key": card.image_key,
        }
        for card in cards
    ]
    statement = pg_insert(TarotCard).values(rows)
    statement = statement.on_conflict_do_update(
        index_elements=[TarotCard.canonical_number],
        set_={
            "name": statement.excluded.name,
            "arcana_type": statement.excluded.arcana_type,
            "suit": statement.excluded.suit,
            "rank": statement.excluded.rank,
            "description": statement.excluded.description,
            "image_key": statement.excluded.image_key,
        },
    )
    await session.execute(statement)


async def _upsert_meanings(session: AsyncSession, cards: tuple) -> None:
    rows = []
    for card in cards:
        for meaning in meanings_for(card):
            rows.append(
                {
                    "card_id": card.id,
                    "orientation": meaning.orientation,
                    "general_meaning": meaning.general_meaning,
                    "keywords": list(meaning.keywords),
                    "love_meaning": meaning.love_meaning,
                    "career_meaning": meaning.career_meaning,
                    "advice": meaning.advice,
                }
            )
    statement = pg_insert(TarotMeaning).values(rows)
    statement = statement.on_conflict_do_update(
        constraint="uq_tarot_meanings_card_orientation",
        set_={
            "general_meaning": statement.excluded.general_meaning,
            "keywords": statement.excluded.keywords,
            "love_meaning": statement.excluded.love_meaning,
            "career_meaning": statement.excluded.career_meaning,
            "advice": statement.excluded.advice,
        },
    )
    await session.execute(statement)


async def _upsert_spreads(session: AsyncSession, spreads: tuple) -> int:
    position_count = 0
    for spread in spreads:
        statement = pg_insert(TarotSpread).values(
            slug=spread.slug,
            name=spread.name,
            description=spread.description,
            card_count=spread.card_count,
        )
        statement = statement.on_conflict_do_update(
            index_elements=[TarotSpread.slug],
            set_={
                "name": statement.excluded.name,
                "description": statement.excluded.description,
                "card_count": statement.excluded.card_count,
            },
        ).returning(TarotSpread.id)
        result = await session.execute(statement)
        spread_id = result.scalar_one()
        await session.execute(
            delete(TarotSpreadPosition).where(TarotSpreadPosition.spread_id == spread_id)
        )
        session.add_all(
            [
                TarotSpreadPosition(
                    spread_id=spread_id,
                    position_index=position.position_index,
                    name=position.name,
                    description=position.description,
                )
                for position in spread.positions
            ]
        )
        position_count += spread.card_count
    await session.flush()
    return position_count


async def _run() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    factory = get_session_factory()
    async with factory() as session:
        summary = await seed_database(session)
        await session.commit()
    print(summary)
    await dispose_engine()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
