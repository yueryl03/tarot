"""Reading requests and the public reading state.

Responses list revealed cards only. Slot indexes that have not been drawn are
reported as occupied or available counts, never as card identities.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.constants import DECK_SIZE, QUESTION_MAX_LENGTH
from app.domain.enums import ArcanaType, DrawMode, Orientation, ReadingStatus, Suit
from app.schemas.spread import SpreadPositionResponse, SpreadResponse


class ReadingCreateRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "question": "What should I know about my relationship?",
                    "spread_slug": "past-present-future",
                    "reversals_enabled": True,
                }
            ]
        }
    )

    question: str = Field(min_length=1, max_length=QUESTION_MAX_LENGTH)
    spread_slug: str = Field(min_length=1, max_length=64)
    reversals_enabled: bool = True

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question must not be blank")
        return stripped


class DrawRequest(BaseModel):
    """Draw from the top of the stored deck, or turn specific face-down slots.

    ``top`` reveals the lowest remaining slot indexes. Slot 0 is the top.
    ``select`` reveals ``slot_indices`` in the order given. Neither mode
    reshuffles the reading.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"mode": "top", "count": 3},
                {"mode": "select", "slot_indices": [12, 40, 7]},
            ]
        }
    )

    mode: DrawMode
    count: int | None = Field(default=None, ge=1, le=DECK_SIZE)
    slot_indices: list[int] | None = None

    @model_validator(mode="after")
    def check_mode_fields(self) -> "DrawRequest":
        if self.mode is DrawMode.TOP:
            if self.count is None:
                raise ValueError("count is required when mode is 'top'")
            if self.slot_indices is not None:
                raise ValueError("slot_indices must be omitted when mode is 'top'")
        elif self.mode is DrawMode.SELECT:
            if not self.slot_indices:
                raise ValueError("slot_indices is required when mode is 'select'")
            if self.count is not None:
                raise ValueError("count must be omitted when mode is 'select'")
        return self


class RevealedCardResponse(BaseModel):
    card_id: int
    card_name: str
    arcana_type: ArcanaType
    suit: Suit | None
    rank: str
    canonical_number: int
    image_key: str | None
    orientation: Orientation
    slot_index: int
    spread_position_index: int
    spread_position_name: str
    spread_position_description: str
    draw_order: int = Field(ge=1)
    revealed_at: datetime
    keywords: list[str]
    general_meaning: str


class ReadingStateResponse(BaseModel):
    reading_id: UUID
    question: str
    status: ReadingStatus
    reversals_enabled: bool
    spread: SpreadResponse
    available_count: int = Field(ge=0, le=DECK_SIZE)
    revealed_slot_indices: list[int]
    remaining_positions: list[SpreadPositionResponse]
    draws: list[RevealedCardResponse]
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class ReadingCreatedResponse(BaseModel):
    """Returned once. ``access_token`` cannot be fetched again."""

    reading_id: UUID
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    question: str
    status: ReadingStatus
    reversals_enabled: bool
    spread: SpreadResponse
    available_count: int = Field(ge=0, le=DECK_SIZE)
    revealed_slot_indices: list[int]
    remaining_positions: list[SpreadPositionResponse]
    draws: list[RevealedCardResponse]
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class DrawResponse(BaseModel):
    """Cards revealed by this request, in reveal order. Not the hidden deck."""

    reading_id: UUID
    status: ReadingStatus
    available_count: int = Field(ge=0, le=DECK_SIZE)
    revealed_slot_indices: list[int]
    completed_at: datetime | None
    draws: list[RevealedCardResponse]


class ReadingDrawsResponse(BaseModel):
    reading_id: UUID
    status: ReadingStatus
    draws: list[RevealedCardResponse]
