"""A completed reading can be interpreted without touching the deck."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.interpretation import Interpretation
from app.repositories.reading_repository import ReadingRepository

pytestmark = pytest.mark.integration


async def _snapshot(session: AsyncSession, reading_id: uuid.UUID) -> tuple:
    repository = ReadingRepository(session)
    slots = await repository.list_slots(reading_id)
    draws = await repository.list_draws(reading_id)
    return (
        tuple((slot.slot_index, slot.card_id, slot.orientation) for slot in slots),
        tuple((draw.deck_slot_id, draw.spread_position_index) for draw in draws),
    )


@pytest.mark.asyncio
async def test_interpretation_does_not_change_the_deck(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    created = await client.post(
        "/api/v1/readings",
        json={
            "question": "What should I know about my relationship?",
            "spread_slug": "past-present-future",
            "reversals_enabled": True,
        },
    )
    assert created.status_code == 201
    body = created.json()
    headers = {"Authorization": f"Bearer {body['access_token']}"}
    reading_id = uuid.UUID(body["reading_id"])
    early = await client.post(f"/api/v1/readings/{reading_id}/interpret", headers=headers)
    assert early.status_code == 409
    assert early.json()["error"]["code"] == "reading_not_complete"
    drawn = await client.post(
        f"/api/v1/readings/{reading_id}/draw",
        headers=headers,
        json={"mode": "select", "slot_indices": [12, 40, 7]},
    )
    assert drawn.status_code == 200
    assert drawn.json()["status"] == "completed"
    async with session_factory() as session:
        before = await _snapshot(session, reading_id)
    interpreted = await client.post(
        f"/api/v1/readings/{reading_id}/interpret",
        headers={**headers, "Idempotency-Key": "interpret-once"},
    )
    assert interpreted.status_code == 200, interpreted.text
    payload = interpreted.json()
    assert payload["provider"] == "mock"
    assert payload["model_name"] == "mock-deterministic-v1"
    assert "DEMONSTRATION ONLY" in payload["interpretation_text"]
    assert "not an intelligent tarot reading" in payload["interpretation_text"]
    assert body["question"] in payload["interpretation_text"]
    for card in drawn.json()["draws"]:
        assert card["card_name"] in payload["interpretation_text"]
        assert card["orientation"] in payload["interpretation_text"]
    assert "symbolic and reflective" in payload["structured_result"]["disclaimer"]
    repeated = await client.post(
        f"/api/v1/readings/{reading_id}/interpret",
        headers={**headers, "Idempotency-Key": "interpret-once"},
    )
    assert repeated.status_code == 200
    assert repeated.json()["id"] == payload["id"]
    fetched = await client.get(
        f"/api/v1/readings/{reading_id}/interpretation",
        headers=headers,
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == payload["id"]
    async with session_factory() as session:
        after = await _snapshot(session, reading_id)
        stored = await session.scalar(
            select(func.count())
            .select_from(Interpretation)
            .where(Interpretation.reading_id == reading_id)
        )
    assert before == after
    assert stored == 1


@pytest.mark.asyncio
async def test_missing_interpretation_is_a_not_found(client: AsyncClient) -> None:
    created = await client.post(
        "/api/v1/readings",
        json={
            "question": "Is there an interpretation yet?",
            "spread_slug": "single-card",
            "reversals_enabled": False,
        },
    )
    headers = {"Authorization": f"Bearer {created.json()['access_token']}"}
    response = await client.get(
        f"/api/v1/readings/{created.json()['reading_id']}/interpretation",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "interpretation_not_found"
