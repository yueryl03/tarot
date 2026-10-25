"""Create a reading and reveal cards from its stored deck."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Response, status

from app.api.deps import get_reading_service, require_bearer
from app.api.errors import ERROR_RESPONSES
from app.schemas.reading import (
    DrawRequest,
    DrawResponse,
    ReadingCreatedResponse,
    ReadingCreateRequest,
    ReadingDrawsResponse,
    ReadingStateResponse,
)
from app.services.reading_service import ReadingService

router = APIRouter(prefix="/readings", tags=["readings"])


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


@router.post(
    "",
    response_model=ReadingCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    responses=ERROR_RESPONSES,
)
async def create_reading(
    body: ReadingCreateRequest,
    response: Response,
    readings: Annotated[ReadingService, Depends(get_reading_service)],
) -> ReadingCreatedResponse:
    """Shuffle a new 78-card deck and return the access token once.

    The token is not stored in recoverable form. Keep it. Unrevealed card
    identities are not included.
    """

    _no_store(response)
    return await readings.create_reading(
        question=body.question,
        spread_slug=body.spread_slug,
        reversals_enabled=body.reversals_enabled,
    )


@router.get(
    "/{reading_id}",
    response_model=ReadingStateResponse,
    responses=ERROR_RESPONSES,
)
async def get_reading(
    reading_id: UUID,
    response: Response,
    token: Annotated[str, Depends(require_bearer)],
    readings: Annotated[ReadingService, Depends(get_reading_service)],
) -> ReadingStateResponse:
    """Return spread progress and cards that have already been revealed."""

    _no_store(response)
    return await readings.get_reading(reading_id, token)


@router.post(
    "/{reading_id}/draw",
    response_model=DrawResponse,
    responses=ERROR_RESPONSES,
)
async def draw_cards(
    reading_id: UUID,
    body: DrawRequest,
    response: Response,
    token: Annotated[str, Depends(require_bearer)],
    readings: Annotated[ReadingService, Depends(get_reading_service)],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> DrawResponse:
    """Reveal cards from the stored deck.

    ``mode=top`` takes the next cards from the top (lowest remaining slot
    index). ``mode=select`` turns the chosen face-down slots in request order.
    A failed request consumes nothing. The same ``Idempotency-Key`` and body
    do not draw again.
    """

    _no_store(response)
    return await readings.draw(reading_id, token, body, idempotency_key)


@router.get(
    "/{reading_id}/draws",
    response_model=ReadingDrawsResponse,
    responses=ERROR_RESPONSES,
)
async def list_draws(
    reading_id: UUID,
    response: Response,
    token: Annotated[str, Depends(require_bearer)],
    readings: Annotated[ReadingService, Depends(get_reading_service)],
) -> ReadingDrawsResponse:
    """Return every card revealed so far, in spread-position order."""

    _no_store(response)
    return await readings.list_draws(reading_id, token)
