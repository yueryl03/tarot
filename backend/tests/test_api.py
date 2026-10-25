"""HTTP contracts, persistence, and reading rules."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.security import verify_access_token
from app.domain.constants import DECK_SIZE
from app.domain.random_source import SequenceRandomSource
from app.models.reading import ReadingSession
from app.models.tarot_card import TarotCard
from app.repositories.reading_repository import ReadingRepository
from app.services.reading_service import ReadingService

pytestmark = pytest.mark.integration

CREATE_KEYS = {
    "reading_id",
    "access_token",
    "token_type",
    "question",
    "status",
    "reversals_enabled",
    "spread",
    "available_count",
    "revealed_slot_indices",
    "remaining_positions",
    "draws",
    "created_at",
    "updated_at",
    "completed_at",
}
STATE_KEYS = CREATE_KEYS - {"access_token", "token_type"}
DRAW_KEYS = {
    "reading_id",
    "status",
    "available_count",
    "revealed_slot_indices",
    "completed_at",
    "draws",
}
REVEALED_KEYS = {
    "card_id",
    "card_name",
    "arcana_type",
    "suit",
    "rank",
    "canonical_number",
    "image_key",
    "orientation",
    "slot_index",
    "spread_position_index",
    "spread_position_name",
    "spread_position_description",
    "draw_order",
    "revealed_at",
    "keywords",
    "general_meaning",
}


async def create_reading(
    client: AsyncClient,
    **overrides: object,
) -> tuple[dict, dict[str, str]]:
    payload = {
        "question": "What should I know about my relationship?",
        "spread_slug": "past-present-future",
        "reversals_enabled": True,
    }
    payload.update(overrides)
    response = await client.post("/api/v1/readings", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    return body, {"Authorization": f"Bearer {body['access_token']}"}


@pytest.mark.asyncio
async def test_health_and_catalog_contract(client: AsyncClient) -> None:
    health = await client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    ready = await client.get("/health/ready")
    assert ready.status_code == 200
    cards = await client.get("/api/v1/cards")
    assert cards.status_code == 200
    catalog = cards.json()["cards"]
    assert len(catalog) == DECK_SIZE
    assert len({card["name"] for card in catalog}) == DECK_SIZE
    assert sum(card["arcana_type"] == "major" for card in catalog) == 22
    assert {meaning["orientation"] for card in catalog for meaning in card["meanings"]} == {
        "upright",
        "reversed",
    }
    spreads = await client.get("/api/v1/spreads")
    assert spreads.status_code == 200
    by_slug = {spread["slug"]: spread for spread in spreads.json()["spreads"]}
    assert set(by_slug) >= {
        "single-card",
        "past-present-future",
        "five-card",
        "celtic-cross",
    }
    assert len(by_slug["celtic-cross"]["positions"]) == 10
    assert by_slug["past-present-future"]["positions"][0]["name"] == "Past"


@pytest.mark.asyncio
async def test_openapi_lists_the_documented_routes(client: AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()
    paths = set(schema["paths"])
    assert "/health" in paths
    assert "/health/ready" in paths
    assert "/api/v1/cards" in paths
    assert "/api/v1/spreads" in paths
    assert "/api/v1/readings" in paths
    assert "/api/v1/readings/{reading_id}" in paths
    assert "/api/v1/readings/{reading_id}/draw" in paths
    assert "/api/v1/readings/{reading_id}/draws" in paths
    assert "/api/v1/readings/{reading_id}/interpret" in paths
    assert "/api/v1/readings/{reading_id}/interpretation" in paths


@pytest.mark.asyncio
async def test_create_hides_the_deck_and_returns_the_token_once(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    cards = (await client.get("/api/v1/cards")).json()["cards"]
    created, _headers = await create_reading(client)
    assert set(created) == CREATE_KEYS
    assert created["token_type"] == "bearer"
    assert created["status"] == "created"
    assert created["available_count"] == DECK_SIZE
    assert created["revealed_slot_indices"] == []
    assert created["draws"] == []
    assert len(created["remaining_positions"]) == 3
    blob = str(created)
    for card in cards:
        assert card["name"] not in blob
        assert card["image_key"] not in blob
    assert "access_token_hash" not in blob
    async with session_factory() as session:
        reading = await session.get(ReadingSession, uuid.UUID(created["reading_id"]))
        assert reading is not None
        assert created["access_token"] not in reading.access_token_hash
        assert verify_access_token(created["access_token"], reading.access_token_hash)
        slots = await ReadingRepository(session).list_slots(reading.id)
    assert len(slots) == DECK_SIZE
    assert len({slot.card_id for slot in slots}) == DECK_SIZE
    assert {slot.orientation for slot in slots} <= {"upright", "reversed"}
    again = await client.get(
        f"/api/v1/readings/{created['reading_id']}",
        headers={"Authorization": f"Bearer {created['access_token']}"},
    )
    assert "access_token" not in again.json()


@pytest.mark.asyncio
async def test_invalid_spread_fails(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/readings",
        json={
            "question": "Will this spread exist?",
            "spread_slug": "not-a-spread",
            "reversals_enabled": True,
        },
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "spread_not_found"


@pytest.mark.asyncio
async def test_unauthorized_access_is_rejected(client: AsyncClient) -> None:
    created, headers = await create_reading(client)
    reading_id = created["reading_id"]
    missing = await client.get(f"/api/v1/readings/{reading_id}")
    assert missing.status_code == 401
    assert missing.json()["error"]["code"] == "unauthorized"
    wrong = await client.get(
        f"/api/v1/readings/{reading_id}",
        headers={"Authorization": "Bearer not-the-token"},
    )
    assert wrong.status_code == 401
    other, other_headers = await create_reading(client, question="A second private question")
    cross = await client.get(
        f"/api/v1/readings/{reading_id}",
        headers=other_headers,
    )
    assert cross.status_code == 401
    absent = await client.get(
        f"/api/v1/readings/{uuid.uuid4()}",
        headers=headers,
    )
    assert absent.status_code == 404
    assert other["question"] not in wrong.text


@pytest.mark.asyncio
async def test_select_assigns_positions_in_request_order_and_can_be_reloaded(
    client: AsyncClient,
) -> None:
    created, headers = await create_reading(client, spread_slug="five-card")
    reading_id = created["reading_id"]
    drawn = await client.post(
        f"/api/v1/readings/{reading_id}/draw",
        headers=headers,
        json={"mode": "select", "slot_indices": [12, 40, 7]},
    )
    assert drawn.status_code == 200, drawn.text
    body = drawn.json()
    assert set(body) == DRAW_KEYS
    assert [card["slot_index"] for card in body["draws"]] == [12, 40, 7]
    assert [card["spread_position_index"] for card in body["draws"]] == [0, 1, 2]
    assert [card["spread_position_name"] for card in body["draws"]] == [
        "Current situation",
        "Challenge",
        "Hidden influence",
    ]
    assert [card["draw_order"] for card in body["draws"]] == [1, 2, 3]
    assert set(body["draws"][0]) == REVEALED_KEYS
    assert body["status"] == "in_progress"
    assert body["available_count"] == DECK_SIZE - 3
    fresh = await client.get(f"/api/v1/readings/{reading_id}", headers=headers)
    assert fresh.status_code == 200
    assert set(fresh.json()) == STATE_KEYS
    assert [card["slot_index"] for card in fresh.json()["draws"]] == [12, 40, 7]
    history = await client.get(f"/api/v1/readings/{reading_id}/draws", headers=headers)
    assert [card["card_id"] for card in history.json()["draws"]] == [
        card["card_id"] for card in body["draws"]
    ]


@pytest.mark.asyncio
async def test_repeated_draws_never_duplicate_and_completion_blocks_another_draw(
    client: AsyncClient,
) -> None:
    created, headers = await create_reading(client)
    reading_id = created["reading_id"]
    first = await client.post(
        f"/api/v1/readings/{reading_id}/draw",
        headers=headers,
        json={"mode": "top", "count": 1},
    )
    assert first.status_code == 200, first.text
    second = await client.post(
        f"/api/v1/readings/{reading_id}/draw",
        headers=headers,
        json={"mode": "top", "count": 2},
    )
    assert second.status_code == 200, second.text
    assert second.json()["status"] == "completed"
    assert len(second.json()["draws"]) == 2
    cards = first.json()["draws"] + second.json()["draws"]
    assert len({card["card_id"] for card in cards}) == 3
    assert len({card["slot_index"] for card in cards}) == 3
    assert [card["slot_index"] for card in cards] == [0, 1, 2]
    again = await client.post(
        f"/api/v1/readings/{reading_id}/draw",
        headers=headers,
        json={"mode": "top", "count": 1},
    )
    assert again.status_code == 409
    assert again.json()["error"]["code"] == "reading_already_completed"


@pytest.mark.asyncio
async def test_invalid_selection_and_duplicate_slots_fail(client: AsyncClient) -> None:
    created, headers = await create_reading(client, spread_slug="five-card")
    url = f"/api/v1/readings/{created['reading_id']}/draw"
    invalid = await client.post(url, headers=headers, json={"mode": "select", "slot_indices": [12, 99]})
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "invalid_slot"
    duplicate = await client.post(
        url,
        headers=headers,
        json={"mode": "select", "slot_indices": [4, 4]},
    )
    assert duplicate.status_code == 422
    assert duplicate.json()["error"]["code"] == "duplicate_slots"
    state = await client.get(f"/api/v1/readings/{created['reading_id']}", headers=headers)
    assert state.json()["draws"] == []


@pytest.mark.asyncio
async def test_drawing_more_than_the_spread_allows_fails(client: AsyncClient) -> None:
    created, headers = await create_reading(client)
    response = await client.post(
        f"/api/v1/readings/{created['reading_id']}/draw",
        headers=headers,
        json={"mode": "top", "count": 4},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "draw_exceeds_spread"
    state = await client.get(f"/api/v1/readings/{created['reading_id']}", headers=headers)
    assert state.json()["available_count"] == DECK_SIZE


@pytest.mark.asyncio
async def test_failed_batch_consumes_no_cards(client: AsyncClient) -> None:
    created, headers = await create_reading(client, spread_slug="five-card")
    url = f"/api/v1/readings/{created['reading_id']}/draw"
    first = await client.post(url, headers=headers, json={"mode": "select", "slot_indices": [1]})
    assert first.status_code == 200
    failed = await client.post(
        url,
        headers=headers,
        json={"mode": "select", "slot_indices": [4, 1, 6]},
    )
    assert failed.status_code == 409
    assert failed.json()["error"]["code"] == "slot_already_revealed"
    state = await client.get(f"/api/v1/readings/{created['reading_id']}", headers=headers)
    assert [card["slot_index"] for card in state.json()["draws"]] == [1]
    assert 4 not in state.json()["revealed_slot_indices"]
    assert 6 not in state.json()["revealed_slot_indices"]


@pytest.mark.asyncio
async def test_idempotency_key_does_not_draw_extra_cards(client: AsyncClient) -> None:
    created, headers = await create_reading(client, spread_slug="five-card")
    url = f"/api/v1/readings/{created['reading_id']}/draw"
    headers = {**headers, "Idempotency-Key": "retry-draw"}
    first = await client.post(url, headers=headers, json={"mode": "select", "slot_indices": [8]})
    second = await client.post(url, headers=headers, json={"mode": "select", "slot_indices": [8]})
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["draws"][0]["card_id"] == second.json()["draws"][0]["card_id"]
    conflict = await client.post(
        url,
        headers=headers,
        json={"mode": "select", "slot_indices": [9]},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "idempotency_conflict"
    state = await client.get(
        f"/api/v1/readings/{created['reading_id']}",
        headers={"Authorization": headers["Authorization"]},
    )
    assert [card["slot_index"] for card in state.json()["draws"]] == [8]


@pytest.mark.asyncio
async def test_reversals_disabled_persists_only_upright_cards(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    created, headers = await create_reading(client, reversals_enabled=False, spread_slug="single-card")
    async with session_factory() as session:
        slots = await ReadingRepository(session).list_slots(uuid.UUID(created["reading_id"]))
    assert {slot.orientation for slot in slots} == {"upright"}
    drawn = await client.post(
        f"/api/v1/readings/{created['reading_id']}/draw",
        headers=headers,
        json={"mode": "top", "count": 1},
    )
    assert drawn.json()["draws"][0]["orientation"] == "upright"
    assert drawn.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_orientation_is_not_resampled_when_a_card_is_revealed(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    script = [0] * (DECK_SIZE - 1) + [1, 0] * (DECK_SIZE // 2)
    rng = SequenceRandomSource(script)
    async with session_factory() as session:
        service = ReadingService(session, rng)
        created = await service.create_reading(
            question="Show me the stored orientation",
            spread_slug="past-present-future",
            reversals_enabled=True,
        )
        assert rng.remaining == 0
        repository = ReadingRepository(session)
        before = [
            (slot.slot_index, slot.card_id, slot.orientation)
            for slot in await repository.list_slots(created.reading_id)
        ]
        from app.schemas.reading import DrawRequest
        from app.domain.enums import DrawMode

        revealed = await service.draw(
            created.reading_id,
            created.access_token,
            DrawRequest(mode=DrawMode.TOP, count=2),
            None,
        )
        after = [
            (slot.slot_index, slot.card_id, slot.orientation)
            for slot in await repository.list_slots(created.reading_id)
        ]
    assert before == after
    assert [card.orientation.value for card in revealed.draws] == ["reversed", "upright"]
    assert rng.remaining == 0


@pytest.mark.asyncio
async def test_two_readings_are_shuffled_independently(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    orders: list[tuple[int, ...]] = []
    async with session_factory() as session:
        service = ReadingService(session)
        for index in range(5):
            created = await service.create_reading(
                question=f"Independent shuffle {index}",
                spread_slug="single-card",
                reversals_enabled=True,
            )
            slots = await ReadingRepository(session).list_slots(created.reading_id)
            orders.append(tuple(slot.card_id for slot in slots))
    assert len(set(orders)) > 1


@pytest.mark.asyncio
async def test_hidden_card_stays_hidden_after_a_partial_draw(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    created, headers = await create_reading(client)
    response = await client.post(
        f"/api/v1/readings/{created['reading_id']}/draw",
        headers=headers,
        json={"mode": "select", "slot_indices": [3]},
    )
    assert response.status_code == 200
    async with session_factory() as session:
        slots = await ReadingRepository(session).list_slots(uuid.UUID(created["reading_id"]))
        hidden = next(slot for slot in slots if slot.slot_index == 0)
        card = await session.get(TarotCard, hidden.card_id)
        assert card is not None
        hidden_name = card.name
        hidden_key = card.image_key
    assert hidden_name not in response.text
    assert hidden_key not in response.text
    assert response.json()["draws"][0]["slot_index"] == 3


@pytest.mark.asyncio
async def test_question_validation_does_not_create_a_reading(
    client: AsyncClient,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    blank = await client.post(
        "/api/v1/readings",
        json={"question": "   ", "spread_slug": "single-card", "reversals_enabled": True},
    )
    assert blank.status_code == 422
    assert blank.json()["error"]["code"] == "validation_error"
    too_long = await client.post(
        "/api/v1/readings",
        json={
            "question": "x" * 2001,
            "spread_slug": "single-card",
            "reversals_enabled": True,
        },
    )
    assert too_long.status_code == 422
    async with session_factory() as session:
        count = await session.scalar(select(func.count()).select_from(ReadingSession))
    assert count == 0
