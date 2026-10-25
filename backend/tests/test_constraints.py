"""Database constraints back up the service rules."""

import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import hash_access_token
from app.core.time import utc_now
from app.models.deck_slot import ReadingDeckSlot
from app.models.reading import ReadingSession
from app.models.spread import TarotSpread
from app.models.tarot_card import TarotCard
from app.services.reading_service import ReadingService

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_commit_rejects_a_reading_that_does_not_have_78_slots(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        spread = (
            await session.execute(select(TarotSpread).where(TarotSpread.slug == "single-card"))
        ).scalar_one()
        card_ids = list(
            (await session.execute(select(TarotCard.id).order_by(TarotCard.id).limit(77))).scalars()
        )
        now = utc_now()
        reading = ReadingSession(
            id=uuid.uuid4(),
            question="This deck is short",
            spread_id=spread.id,
            status="created",
            reversals_enabled=True,
            access_token_hash=hash_access_token("unused-token"),
            created_at=now,
            updated_at=now,
        )
        session.add(reading)
        await session.flush()
        session.add_all(
            [
                ReadingDeckSlot(
                    id=uuid.uuid4(),
                    reading_id=reading.id,
                    card_id=card_id,
                    slot_index=index,
                    orientation="upright",
                )
                for index, card_id in enumerate(card_ids)
            ]
        )
        with pytest.raises(Exception) as caught:
            await session.commit()
        assert "exactly 78" in str(caught.value)
        await session.rollback()


@pytest.mark.asyncio
async def test_reversals_disabled_cannot_store_a_reversed_slot(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        spread = (
            await session.execute(select(TarotSpread).where(TarotSpread.slug == "single-card"))
        ).scalar_one()
        card_id = (await session.execute(select(TarotCard.id).limit(1))).scalar_one()
        now = utc_now()
        reading = ReadingSession(
            id=uuid.uuid4(),
            question="No reversals",
            spread_id=spread.id,
            status="created",
            reversals_enabled=False,
            access_token_hash=hash_access_token("unused-token"),
            created_at=now,
            updated_at=now,
        )
        session.add(reading)
        await session.flush()
        session.add(
            ReadingDeckSlot(
                id=uuid.uuid4(),
                reading_id=reading.id,
                card_id=card_id,
                slot_index=0,
                orientation="reversed",
            )
        )
        with pytest.raises(Exception) as caught:
            await session.flush()
        assert "upright" in str(caught.value)
        await session.rollback()


@pytest.mark.asyncio
async def test_stored_deck_slots_are_immutable_and_positions_stay_in_range(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        created = await ReadingService(session).create_reading(
            question="Protect the stored deck",
            spread_slug="past-present-future",
            reversals_enabled=True,
        )
        with pytest.raises(Exception) as mutated:
            await session.execute(
                text(
                    """
                    UPDATE reading_deck_slots
                    SET orientation = CASE
                        WHEN orientation = 'upright' THEN 'reversed'
                        ELSE 'upright'
                    END
                    WHERE reading_id = :reading_id AND slot_index = 0
                    """
                ),
                {"reading_id": created.reading_id},
            )
        assert "immutable" in str(mutated.value)
        await session.rollback()

    async with session_factory() as session:
        created = await ReadingService(session).create_reading(
            question="Protect the spread size",
            spread_slug="past-present-future",
            reversals_enabled=True,
        )
        slot_id = (
            await session.execute(
                text(
                    """
                    SELECT id FROM reading_deck_slots
                    WHERE reading_id = :reading_id AND slot_index = 0
                    """
                ),
                {"reading_id": created.reading_id},
            )
        ).scalar_one()
        with pytest.raises(Exception) as out_of_range:
            await session.execute(
                text(
                    """
                    INSERT INTO reading_draws (
                        id, reading_id, deck_slot_id, spread_position_index, revealed_at
                    )
                    VALUES (:id, :reading_id, :slot_id, 3, CURRENT_TIMESTAMP)
                    """
                ),
                {
                    "id": uuid.uuid4(),
                    "reading_id": created.reading_id,
                    "slot_id": slot_id,
                },
            )
        assert "outside" in str(out_of_range.value)
        await session.rollback()
