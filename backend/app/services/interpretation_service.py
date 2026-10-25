"""Store an interpretation of a completed reading.

The provider does not receive a database session. This service writes an
interpretation row and does not update deck slots, orientations, or draws.
"""

import logging
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.base import InterpretationProvider
from app.core.security import canonical_request_hash, clean_idempotency_key
from app.core.time import utc_now
from app.domain.enums import ReadingStatus
from app.domain.errors import TarotError
from app.domain.interpretation import StructuredInterpretation
from app.models.idempotency import IdempotencyKey
from app.models.interpretation import Interpretation
from app.schemas.interpretation import InterpretationResponse
from app.services.reading_service import ReadingService

logger = logging.getLogger(__name__)

_INTERPRET_OPERATION = "interpret"


class _NoRandom:
    """Refuses to supply randomness. Interpretation must not shuffle."""

    def randbelow(self, exclusive_upper: int) -> int:
        raise TarotError(
            "Interpretation cannot shuffle or select cards.",
            code="deck_integrity",
        )


class InterpretationService:
    def __init__(
        self,
        session: AsyncSession,
        provider: InterpretationProvider,
    ) -> None:
        self.session = session
        self.provider = provider
        self.readings = ReadingService(session, _NoRandom())

    async def interpret(
        self,
        reading_id: UUID,
        token: str,
        idempotency_key: str | None,
    ) -> InterpretationResponse:
        key = clean_idempotency_key(idempotency_key)
        request_hash = canonical_request_hash({"operation": _INTERPRET_OPERATION})
        await self.readings._require_reading(reading_id, token)
        try:
            reading = await self.readings._lock_reading(reading_id)
            if key is not None:
                existing = await self.readings.readings.get_idempotency(
                    reading_id,
                    _INTERPRET_OPERATION,
                    key,
                )
                if existing is not None:
                    if existing.request_hash != request_hash:
                        raise TarotError(
                            "This idempotency key was already used with a different request.",
                            code="idempotency_conflict",
                        )
                    stored = dict(existing.response_body)
                    await self.session.rollback()
                    return InterpretationResponse.model_validate(stored)
            if reading.status != ReadingStatus.COMPLETED.value:
                raise TarotError(
                    "Interpretation is available after every spread position has a card.",
                    code="reading_not_complete",
                )
            request = await self.readings.build_interpretation_request(reading)
            generated = await self.provider.generate_reading(request)
            row = Interpretation(
                id=uuid4(),
                reading_id=reading.id,
                model_name=generated.model_name,
                provider=generated.provider,
                interpretation_text=generated.interpretation_text,
                structured_result=generated.structured_result.model_dump(mode="json"),
                created_at=utc_now(),
            )
            self.session.add(row)
            response = _response(row)
            if key is not None:
                self.session.add(
                    IdempotencyKey(
                        id=uuid4(),
                        reading_id=reading.id,
                        operation=_INTERPRET_OPERATION,
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
        logger.info(
            "interpretation_stored",
            extra={
                "reading_id": str(reading_id),
                "operation": "interpret",
            },
        )
        return response

    async def get_latest(
        self,
        reading_id: UUID,
        token: str,
    ) -> InterpretationResponse:
        await self.readings._require_reading(reading_id, token)
        statement = (
            select(Interpretation)
            .where(Interpretation.reading_id == reading_id)
            .order_by(Interpretation.created_at.desc(), Interpretation.id.desc())
            .limit(1)
        )
        result = await self.session.execute(statement)
        row = result.scalar_one_or_none()
        if row is None or row.structured_result is None:
            raise TarotError(
                "No interpretation has been stored for this reading.",
                code="interpretation_not_found",
            )
        return _response(row)


def _response(row: Interpretation) -> InterpretationResponse:
    structured = StructuredInterpretation.model_validate(row.structured_result)
    return InterpretationResponse(
        id=row.id,
        reading_id=row.reading_id,
        provider=row.provider,
        model_name=row.model_name,
        interpretation_text=row.interpretation_text,
        structured_result=structured,
        created_at=row.created_at,
    )
