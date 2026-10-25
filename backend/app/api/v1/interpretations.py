"""Interpretation routes. They do not draw or reshuffle."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Response

from app.api.deps import get_interpretation_service, require_bearer
from app.api.errors import ERROR_RESPONSES
from app.schemas.interpretation import InterpretationResponse
from app.services.interpretation_service import InterpretationService

router = APIRouter(prefix="/readings", tags=["interpretations"])


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


@router.post(
    "/{reading_id}/interpret",
    response_model=InterpretationResponse,
    responses=ERROR_RESPONSES,
)
async def interpret_reading(
    reading_id: UUID,
    response: Response,
    token: Annotated[str, Depends(require_bearer)],
    interpretations: Annotated[
        InterpretationService,
        Depends(get_interpretation_service),
    ],
    idempotency_key: Annotated[str | None, Header()] = None,
) -> InterpretationResponse:
    """Interpret a completed reading. The deck is not modified."""

    _no_store(response)
    return await interpretations.interpret(reading_id, token, idempotency_key)


@router.get(
    "/{reading_id}/interpretation",
    response_model=InterpretationResponse,
    responses=ERROR_RESPONSES,
)
async def get_interpretation(
    reading_id: UUID,
    response: Response,
    token: Annotated[str, Depends(require_bearer)],
    interpretations: Annotated[
        InterpretationService,
        Depends(get_interpretation_service),
    ],
) -> InterpretationResponse:
    """Return the most recent stored interpretation."""

    _no_store(response)
    return await interpretations.get_latest(reading_id, token)
