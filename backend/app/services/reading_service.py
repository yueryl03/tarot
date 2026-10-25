"""Reading lifecycle.

Creating a reading shuffles once and stores all 78 slots. Later draws only
reveal stored slots. This module never calls the shuffle service from a draw,
and it never logs the raw access token.
"""

import logging
import uuid
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import app.models  # noqa: F401
from app.ai.base import CardReadingContext, InterpretationRequest

from app.core.security import (
    DUMMY_TOKEN_HASH,
    canonical_request_hash,
    clean_idempotency_key,
    generate_access_token,
    hash_access_token,
    verify_access_token,
)
from app.core.time import utc_now
from app.domain.constants import DECK_SIZE, QUESTION_MAX_LENGTH
from app.domain.enums import DrawMode, ReadingStatus
from app.domain.errors import TarotError
from app.domain.random_source import RandomSource
from app.models.deck_slot import ReadingDeckSlot
from app.models.idempotency import IdempotencyKey
from app.models.reading import ReadingSession
from app.models.reading_draw import ReadingDraw
from app.models.spread import TarotSpread, TarotSpreadPosition
from app.models.tarot_card import TarotCard
from app.repositories.card_repository import CardRepository
from app.repositories.reading_repository import ReadingRepository
from app.schemas.reading import (
    DrawRequest,
    DrawResponse,
    ReadingCreatedResponse,
    ReadingDrawsResponse,
    ReadingStateResponse,
    RevealedCardResponse,
)
from app.schemas.spread import SpreadPositionResponse, SpreadResponse
from app.services.shuffle_service import ShuffleService
from app.services.spread_service import SpreadService

logger = logging.getLogger(__name__)

_MISSING_MEANING = "No meaning row is stored for this card and orientation."
_DRAW_OPERATION = "draw"


class ReadingService:
    def __init__(self, session: AsyncSession, rng: RandomSource | None = None) -> None:
        self.session = session
        self.cards = CardRepository(session)
        self.readings = ReadingRepository(session)
        self.spreads = SpreadService(session)
        self.shuffle = ShuffleService(rng)

    async def create_reading(
        self,
        *,
        question: str,
        spread_slug: str,
        reversals_enabled: bool,
    ) -> ReadingCreatedResponse:
        cleaned = question.strip()
        if not cleaned or len(cleaned) > QUESTION_MAX_LENGTH:
            raise TarotError(
                "Question must be between 1 and 2000 characters.",
                code="validation_error",
            )
        spread = await self.spreads.require_by_slug(spread_slug)
        card_ids = await self.cards.list_ids()
        if len(card_ids) != DECK_SIZE or len(set(card_ids)) != DECK_SIZE:
            raise TarotError(
                "The card catalog must contain exactly 78 unique cards before a reading can be shuffled.",
                code="deck_integrity",
                details={"card_count": len(card_ids)},
            )
        deck = self.shuffle.shuffle_new_deck(
            card_ids,
            reversals_enabled=reversals_enabled,
        )
        token = generate_access_token()
        now = utc_now()
        reading = ReadingSession(
            id=uuid4(),
            question=cleaned,
            spread_id=spread.id,
            status=ReadingStatus.CREATED.value,
            reversals_enabled=reversals_enabled,
            access_token_hash=hash_access_token(token),
            created_at=now,
            updated_at=now,
        )
        try:
            self.session.add(reading)
            await self.session.flush()
            self.session.add_all(
                [
                    ReadingDeckSlot(
                        id=uuid4(),
                        reading_id=reading.id,
                        card_id=slot.card_id,
                        slot_index=slot.slot_index,
                        orientation=slot.orientation.value,
                    )
                    for slot in deck.slots
                ]
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        logger.info(
            "reading_created",
            extra={
                "reading_id": str(reading.id),
                "spread_slug": spread.slug,
                "operation": "create_reading",
            },
        )
        state = await self._state(reading, spread)
        return ReadingCreatedResponse.model_validate(
            {**state.model_dump(), "access_token": token, "token_type": "bearer"}
        )

    async def get_reading(self, reading_id: UUID, token: str) -> ReadingStateResponse:
        reading = await self._require_reading(reading_id, token)
        spread = await self.spreads.require_by_id(reading.spread_id)
        return await self._state(reading, spread)

    async def list_draws(self, reading_id: UUID, token: str) -> ReadingDrawsResponse:
        reading = await self._require_reading(reading_id, token)
        spread = await self.spreads.require_by_id(reading.spread_id)
        draws = await self._revealed_cards(reading.id, spread)
        return ReadingDrawsResponse(
            reading_id=reading.id,
            status=ReadingStatus(reading.status),
            draws=draws,
        )

    async def draw(
        self,
        reading_id: UUID,
        token: str,
        body: DrawRequest,
        idempotency_key: str | None,
    ) -> DrawResponse:
        key = clean_idempotency_key(idempotency_key)
        request_hash = canonical_request_hash(
            {
                "mode": body.mode.value,
                "count": body.count,
                "slot_indices": list(body.slot_indices) if body.slot_indices is not None else None,
            }
        )
        await self._require_reading(reading_id, token)
        try:
            reading = await self._lock_reading(reading_id)
            if key is not None:
                existing = await self.readings.get_idempotency(
                    reading_id, _DRAW_OPERATION, key
                )
                if existing is not None:
                    if existing.request_hash != request_hash:
                        raise TarotError(
                            "This idempotency key was already used with a different request.",
                            code="idempotency_conflict",
                        )
                    stored = dict(existing.response_body)
                    await self.session.rollback()
                    return DrawResponse.model_validate(stored)

            spread = await self.spreads.require_by_id(reading.spread_id)
            existing_draws = await self.readings.count_draws(reading_id)
            if (
                reading.status == ReadingStatus.COMPLETED.value
                or existing_draws >= spread.card_count
            ):
                raise TarotError(
                    "This reading is already complete.",
                    code="reading_already_completed",
                    details={"spread_card_count": spread.card_count},
                )
            revealed = await self.readings.revealed_slot_indexes(reading_id)
            plan = self.shuffle.engine.plan_draw(
                mode=DrawMode(body.mode),
                count=body.count,
                slot_indices=body.slot_indices,
                revealed_slots=revealed,
                next_position_index=existing_draws,
                spread_card_count=spread.card_count,
            )
            slots = await self.readings.slots_by_indexes(
                reading_id,
                [item.slot_index for item in plan],
            )
            slot_by_index = {slot.slot_index: slot for slot in slots}
            if len(slot_by_index) != len(plan):
                raise TarotError(
                    "The stored deck is missing a requested slot.",
                    code="deck_integrity",
                )
            cards = await self.cards.get_by_ids(
                [slot.card_id for slot in slot_by_index.values()]
            )
            positions = {item.position_index: item for item in spread.positions}
            now = utc_now()
            new_draws: list[RevealedCardResponse] = []
            for planned in plan:
                slot = slot_by_index[planned.slot_index]
                card = cards.get(slot.card_id)
                position = positions.get(planned.spread_position_index)
                if card is None or position is None:
                    raise TarotError(
                        "The stored deck or spread is incomplete.",
                        code="deck_integrity",
                    )
                draw = ReadingDraw(
                    id=uuid4(),
                    reading_id=reading.id,
                    deck_slot_id=slot.id,
                    spread_position_index=planned.spread_position_index,
                    revealed_at=now,
                )
                self.session.add(draw)
                new_draws.append(
                    _revealed_card(
                        card=card,
                        slot=slot,
                        position=position,
                        revealed_at=now,
                    )
                )
            total = existing_draws + len(plan)
            if total == spread.card_count:
                reading.status = ReadingStatus.COMPLETED.value
                reading.completed_at = now
            elif reading.status == ReadingStatus.CREATED.value:
                reading.status = ReadingStatus.IN_PROGRESS.value
            reading.updated_at = now
            all_revealed = sorted(revealed | {item.slot_index for item in plan})
            response = DrawResponse(
                reading_id=reading.id,
                status=ReadingStatus(reading.status),
                available_count=DECK_SIZE - len(all_revealed),
                revealed_slot_indices=all_revealed,
                completed_at=reading.completed_at,
                draws=new_draws,
            )
            if key is not None:
                self.session.add(
                    IdempotencyKey(
                        id=uuid4(),
                        reading_id=reading.id,
                        operation=_DRAW_OPERATION,
                        idempotency_key=key,
                        request_hash=request_hash,
                        status_code=200,
                        response_body=response.model_dump(mode="json"),
                    )
                )
            await self.session.commit()
        except TarotError:
            await self.session.rollback()
            raise
        except IntegrityError as exc:
            await self.session.rollback()
            logger.exception(
                "reading_draw_conflict",
                extra={"reading_id": str(reading_id), "operation": "draw"},
            )
            raise TarotError(
                "The reading was updated concurrently. Retry the request.",
                code="concurrent_conflict",
            ) from exc
        logger.info(
            "cards_revealed",
            extra={
                "reading_id": str(reading_id),
                "operation": "draw",
                "draw_count": len(response.draws),
            },
        )
        return response

    async def _require_reading(self, reading_id: UUID, token: str) -> ReadingSession:
        reading = await self.readings.get(reading_id)
        if reading is None:
            verify_access_token(token, DUMMY_TOKEN_HASH)
            raise TarotError("Reading not found.", code="reading_not_found")
        if not verify_access_token(token, reading.access_token_hash):
            raise TarotError(
                "The reading token is invalid.",
                code="unauthorized",
            )
        return reading

    async def _lock_reading(self, reading_id: UUID) -> ReadingSession:
        reading = await self.readings.get_for_update(reading_id)
        if reading is None:
            raise TarotError("Reading not found.", code="reading_not_found")
        return reading

    async def _state(
        self,
        reading: ReadingSession,
        spread: TarotSpread,
    ) -> ReadingStateResponse:
        draws = await self._revealed_cards(reading.id, spread)
        revealed = sorted({draw.slot_index for draw in draws})
        drawn_positions = {draw.spread_position_index for draw in draws}
        remaining = [
            SpreadPositionResponse.model_validate(position)
            for position in spread.positions
            if position.position_index not in drawn_positions
        ]
        return ReadingStateResponse(
            reading_id=reading.id,
            question=reading.question,
            status=ReadingStatus(reading.status),
            reversals_enabled=reading.reversals_enabled,
            spread=SpreadResponse.model_validate(spread),
            available_count=DECK_SIZE - len(revealed),
            revealed_slot_indices=revealed,
            remaining_positions=remaining,
            draws=draws,
            created_at=reading.created_at,
            updated_at=reading.updated_at,
            completed_at=reading.completed_at,
        )

    async def _revealed_cards(
        self,
        reading_id: uuid.UUID,
        spread: TarotSpread,
    ) -> list[RevealedCardResponse]:
        draws = await self.readings.list_draws(reading_id)
        if not draws:
            return []
        slot_rows = await self._slots_for_draws(reading_id, draws)
        slot_by_id = {slot.id: slot for slot in slot_rows}
        cards = await self.cards.get_by_ids([slot.card_id for slot in slot_rows])
        positions = {item.position_index: item for item in spread.positions}
        revealed: list[RevealedCardResponse] = []
        for draw in draws:
            slot = slot_by_id.get(draw.deck_slot_id)
            if slot is None:
                raise TarotError(
                    "A revealed draw is missing its deck slot.",
                    code="deck_integrity",
                )
            card = cards.get(slot.card_id)
            position = positions.get(draw.spread_position_index)
            if card is None or position is None:
                raise TarotError(
                    "A revealed card is missing catalog or spread data.",
                    code="deck_integrity",
                )
            revealed.append(
                _revealed_card(
                    card=card,
                    slot=slot,
                    position=position,
                    revealed_at=draw.revealed_at,
                )
            )
        return revealed

    async def build_interpretation_request(
        self,
        reading: ReadingSession,
    ) -> InterpretationRequest:
        """Assemble the provider input from stored cards. Does not shuffle."""

        spread = await self.spreads.require_by_id(reading.spread_id)
        draws = await self.readings.list_draws(reading.id)
        if len(draws) != spread.card_count:
            raise TarotError(
                "The reading is marked complete but is missing draws.",
                code="deck_integrity",
            )
        slot_rows = await self._slots_for_draws(reading.id, draws)
        slot_by_id = {slot.id: slot for slot in slot_rows}
        cards = await self.cards.get_by_ids([slot.card_id for slot in slot_rows])
        positions = {item.position_index: item for item in spread.positions}
        contexts: list[CardReadingContext] = []
        for draw in draws:
            slot = slot_by_id.get(draw.deck_slot_id)
            if slot is None:
                raise TarotError(
                    "A revealed draw is missing its deck slot.",
                    code="deck_integrity",
                )
            card = cards.get(slot.card_id)
            position = positions.get(draw.spread_position_index)
            if card is None or position is None:
                raise TarotError(
                    "A revealed card is missing catalog or spread data.",
                    code="deck_integrity",
                )
            meaning = _meaning_row(card, slot.orientation)
            contexts.append(
                CardReadingContext(
                    position_index=position.position_index,
                    position_name=position.name,
                    position_description=position.description,
                    card_id=card.id,
                    card_name=card.name,
                    arcana_type=card.arcana_type,
                    suit=card.suit,
                    rank=card.rank,
                    orientation=slot.orientation,
                    general_meaning=meaning.general_meaning if meaning else _MISSING_MEANING,
                    keywords=tuple(str(item) for item in meaning.keywords) if meaning else (),
                    love_meaning=meaning.love_meaning if meaning else None,
                    career_meaning=meaning.career_meaning if meaning else None,
                    advice=meaning.advice if meaning else None,
                )
            )
        return InterpretationRequest(
            question=reading.question,
            spread_name=spread.name,
            spread_description=spread.description,
            cards=tuple(contexts),
        )

    async def _slots_for_draws(
        self,
        reading_id: uuid.UUID,
        draws: list[ReadingDraw],
    ) -> list[ReadingDeckSlot]:
        slot_ids = [draw.deck_slot_id for draw in draws]
        statement = select(ReadingDeckSlot).where(
            ReadingDeckSlot.reading_id == reading_id,
            ReadingDeckSlot.id.in_(slot_ids),
        )
        result = await self.session.execute(statement)
        return list(result.scalars().all())


def _revealed_card(
    *,
    card: TarotCard,
    slot: ReadingDeckSlot,
    position: TarotSpreadPosition,
    revealed_at,
) -> RevealedCardResponse:
    keywords, general = _meaning(card, slot.orientation)
    return RevealedCardResponse(
        card_id=card.id,
        card_name=card.name,
        arcana_type=card.arcana_type,  # type: ignore[arg-type]
        suit=card.suit,  # type: ignore[arg-type]
        rank=card.rank,
        canonical_number=card.canonical_number,
        image_key=card.image_key,
        orientation=slot.orientation,  # type: ignore[arg-type]
        slot_index=slot.slot_index,
        spread_position_index=position.position_index,
        spread_position_name=position.name,
        spread_position_description=position.description,
        draw_order=position.position_index + 1,
        revealed_at=revealed_at,
        keywords=keywords,
        general_meaning=general,
    )


def _meaning(card: TarotCard, orientation: str) -> tuple[list[str], str]:
    meaning = _meaning_row(card, orientation)
    if meaning is None:
        return [], _MISSING_MEANING
    raw_keywords = meaning.keywords
    keywords = [str(item) for item in raw_keywords] if raw_keywords else []
    return keywords, meaning.general_meaning


def _meaning_row(card: TarotCard, orientation: str):
    for meaning in card.meanings:
        if meaning.orientation == orientation:
            return meaning
    return None
