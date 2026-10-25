"""Reading, deck, draw, and idempotency persistence."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.deck_slot import ReadingDeckSlot
from app.models.idempotency import IdempotencyKey
from app.models.reading import ReadingSession
from app.models.reading_draw import ReadingDraw


class ReadingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, reading_id: uuid.UUID) -> ReadingSession | None:
        return await self.session.get(ReadingSession, reading_id)

    async def get_for_update(self, reading_id: uuid.UUID) -> ReadingSession | None:
        statement = (
            select(ReadingSession)
            .where(ReadingSession.id == reading_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def count_draws(self, reading_id: uuid.UUID) -> int:
        statement = (
            select(func.count())
            .select_from(ReadingDraw)
            .where(ReadingDraw.reading_id == reading_id)
        )
        value = await self.session.scalar(statement)
        return int(value or 0)

    async def revealed_slot_indexes(self, reading_id: uuid.UUID) -> set[int]:
        statement = (
            select(ReadingDeckSlot.slot_index)
            .join(ReadingDraw, ReadingDraw.deck_slot_id == ReadingDeckSlot.id)
            .where(ReadingDraw.reading_id == reading_id)
        )
        result = await self.session.execute(statement)
        return set(result.scalars().all())

    async def slots_by_indexes(
        self,
        reading_id: uuid.UUID,
        slot_indexes: list[int],
    ) -> list[ReadingDeckSlot]:
        if not slot_indexes:
            return []
        statement = select(ReadingDeckSlot).where(
            ReadingDeckSlot.reading_id == reading_id,
            ReadingDeckSlot.slot_index.in_(slot_indexes),
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_slots(self, reading_id: uuid.UUID) -> list[ReadingDeckSlot]:
        statement = (
            select(ReadingDeckSlot)
            .where(ReadingDeckSlot.reading_id == reading_id)
            .order_by(ReadingDeckSlot.slot_index)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def list_draws(self, reading_id: uuid.UUID) -> list[ReadingDraw]:
        statement = (
            select(ReadingDraw)
            .where(ReadingDraw.reading_id == reading_id)
            .order_by(ReadingDraw.spread_position_index)
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def get_idempotency(
        self,
        reading_id: uuid.UUID,
        operation: str,
        key: str,
    ) -> IdempotencyKey | None:
        statement = select(IdempotencyKey).where(
            IdempotencyKey.reading_id == reading_id,
            IdempotencyKey.operation == operation,
            IdempotencyKey.idempotency_key == key,
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
