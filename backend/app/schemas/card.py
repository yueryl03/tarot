"""Card catalog responses. These are not shuffled deck slots."""

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ArcanaType, Orientation, Suit


class MeaningResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    orientation: Orientation
    general_meaning: str
    keywords: list[str]
    love_meaning: str | None = None
    career_meaning: str | None = None
    advice: str | None = None


class CardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    arcana_type: ArcanaType
    suit: Suit | None = None
    rank: str
    canonical_number: int = Field(ge=0, le=77)
    description: str | None = None
    image_key: str | None = None
    meanings: list[MeaningResponse]


class CardListResponse(BaseModel):
    cards: list[CardResponse]
