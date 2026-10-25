"""Public card catalog."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.card_repository import CardRepository
from app.schemas.card import CardListResponse, CardResponse

router = APIRouter(prefix="/cards", tags=["cards"])


@router.get("", response_model=CardListResponse)
async def list_cards(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> CardListResponse:
    """Return the 78-card catalog. This is not a shuffled reading deck."""

    cards = await CardRepository(session).list_cards()
    return CardListResponse(
        cards=[CardResponse.model_validate(card) for card in cards]
    )
