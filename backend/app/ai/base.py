"""Provider contract. Implementations must not receive a database session."""

from dataclasses import dataclass
from typing import Protocol

from app.domain.interpretation import StructuredInterpretation


@dataclass(frozen=True, slots=True)
class CardReadingContext:
    position_index: int
    position_name: str
    position_description: str
    card_id: int
    card_name: str
    arcana_type: str
    suit: str | None
    rank: str
    orientation: str
    general_meaning: str
    keywords: tuple[str, ...]
    love_meaning: str | None
    career_meaning: str | None
    advice: str | None


@dataclass(frozen=True, slots=True)
class InterpretationRequest:
    question: str
    spread_name: str
    spread_description: str
    cards: tuple[CardReadingContext, ...]


@dataclass(frozen=True, slots=True)
class GeneratedInterpretation:
    provider: str
    model_name: str
    interpretation_text: str
    structured_result: StructuredInterpretation


class InterpretationProvider(Protocol):
    """Generate a symbolic reading from cards that were already drawn."""

    provider_name: str
    model_name: str

    async def generate_reading(
        self,
        request: InterpretationRequest,
    ) -> GeneratedInterpretation:
        """Return an interpretation. Do not change cards, orientation, or position."""
