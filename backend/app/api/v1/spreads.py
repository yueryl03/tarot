"""Public spread catalog."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.spread import SpreadListResponse, SpreadResponse
from app.services.spread_service import SpreadService

router = APIRouter(prefix="/spreads", tags=["spreads"])


@router.get("", response_model=SpreadListResponse)
async def list_spreads(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SpreadListResponse:
    """Return every spread and its positions. Card limits come from this data."""

    spreads = await SpreadService(session).list_spreads()
    return SpreadListResponse(
        spreads=[SpreadResponse.model_validate(spread) for spread in spreads]
    )
