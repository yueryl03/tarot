"""Row locks keep concurrent draws from consuming the same card."""

import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.domain.enums import DrawMode
from app.domain.errors import TarotError
from app.repositories.reading_repository import ReadingRepository
from app.schemas.reading import DrawRequest
from app.services.reading_service import ReadingService

pytestmark = pytest.mark.integration


async def _create(session_factory: async_sessionmaker[AsyncSession], slug: str):
    async with session_factory() as session:
        created = await ReadingService(session).create_reading(
            question="Can two requests reveal the same card?",
            spread_slug=slug,
            reversals_enabled=True,
        )
    return created


@pytest.mark.asyncio
async def test_concurrent_top_draws_cannot_duplicate_slots(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    created = await _create(session_factory, "past-present-future")

    async def draw_one() -> tuple[str, object]:
        async with session_factory() as session:
            service = ReadingService(session)
            try:
                result = await service.draw(
                    created.reading_id,
                    created.access_token,
                    DrawRequest(mode=DrawMode.TOP, count=1),
                    None,
                )
            except TarotError as exc:
                return ("err", exc.code)
            return ("ok", result.draws[0].slot_index)

    results = await asyncio.gather(*(draw_one() for _ in range(4)))
    ok_slots = [slot for status, slot in results if status == "ok"]
    errors = [code for status, code in results if status == "err"]
    assert len(ok_slots) == 3
    assert errors == ["reading_already_completed"]
    assert len(set(ok_slots)) == 3
    async with session_factory() as session:
        repository = ReadingRepository(session)
        assert await repository.count_draws(created.reading_id) == 3
        assert len(await repository.revealed_slot_indexes(created.reading_id)) == 3


@pytest.mark.asyncio
async def test_concurrent_overlapping_select_is_all_or_nothing(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    created = await _create(session_factory, "five-card")

    async def select_same() -> tuple[str, str]:
        async with session_factory() as session:
            service = ReadingService(session)
            try:
                result = await service.draw(
                    created.reading_id,
                    created.access_token,
                    DrawRequest(mode=DrawMode.SELECT, slot_indices=[0, 1]),
                    None,
                )
            except TarotError as exc:
                return ("err", exc.code)
            return ("ok", ",".join(str(card.slot_index) for card in result.draws))

    results = await asyncio.gather(select_same(), select_same())
    assert sorted(status for status, _code in results) == ["err", "ok"]
    assert dict(results)["err"] == "slot_already_revealed" or any(
        code == "slot_already_revealed" for status, code in results if status == "err"
    )
    async with session_factory() as session:
        repository = ReadingRepository(session)
        assert await repository.count_draws(created.reading_id) == 2
        assert await repository.revealed_slot_indexes(created.reading_id) == {0, 1}


@pytest.mark.asyncio
async def test_concurrent_same_idempotency_key_draws_once(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    created = await _create(session_factory, "five-card")

    async def select_with_key() -> tuple[str, tuple[int, ...]]:
        async with session_factory() as session:
            service = ReadingService(session)
            try:
                result = await service.draw(
                    created.reading_id,
                    created.access_token,
                    DrawRequest(mode=DrawMode.SELECT, slot_indices=[3, 4]),
                    "same-key",
                )
            except TarotError as exc:
                return ("err", (exc.code,))  # type: ignore[return-value]
            return ("ok", tuple(card.slot_index for card in result.draws))

    results = await asyncio.gather(select_with_key(), select_with_key())
    assert [status for status, _payload in results] == ["ok", "ok"]
    assert results[0][1] == results[1][1] == (3, 4)
    async with session_factory() as session:
        assert await ReadingRepository(session).count_draws(created.reading_id) == 2
