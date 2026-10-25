"""Structured interpretation contract shared by providers and the API.

Providers may only fill this structure. They do not receive a way to change
card identity, orientation, spread position, or the stored deck.
"""

from pydantic import BaseModel, ConfigDict, Field


class CardInterpretation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    position_index: int = Field(ge=0)
    position_name: str
    card_name: str
    orientation: str
    interpretation: str


class StructuredInterpretation(BaseModel):
    """Symbolic reading. Not a factual prediction."""

    model_config = ConfigDict(extra="forbid")

    card_interpretations: list[CardInterpretation]
    relationships: str
    overall: str
    guidance: str
    disclaimer: str


SYMBOLIC_DISCLAIMER = (
    "Tarot interpretations are symbolic and reflective. They are not verified "
    "predictions, diagnoses, or facts about another person's thoughts, "
    "intentions, or future."
)


def render_interpretation_text(structured: StructuredInterpretation) -> str:
    """Render the structured reading as plain text for storage and display."""

    lines = [
        structured.overall,
        "",
        "Guidance",
        structured.guidance,
        "",
        "Relationships",
        structured.relationships,
        "",
    ]
    for card in structured.card_interpretations:
        lines.append(
            f"{card.position_name}: {card.card_name} ({card.orientation})"
        )
        lines.append(card.interpretation)
        lines.append("")
    lines.append(structured.disclaimer)
    return "\n".join(lines).strip()
