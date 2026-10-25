"""Spread responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SpreadPositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position_index: int = Field(ge=0)
    name: str
    description: str


class SpreadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: str
    card_count: int = Field(ge=1)
    created_at: datetime
    positions: list[SpreadPositionResponse]


class SpreadListResponse(BaseModel):
    spreads: list[SpreadResponse]
