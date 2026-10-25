"""Deterministic stand-in for a language model.

The result is labelled as a demonstration. It is built only from the request,
so the same completed reading always produces the same text. It does not call
a network and it does not choose cards.
"""

from app.ai.base import GeneratedInterpretation, InterpretationRequest
from app.ai.prompt_builder import build_messages
from app.domain.interpretation import (
    SYMBOLIC_DISCLAIMER,
    CardInterpretation,
    StructuredInterpretation,
    render_interpretation_text,
)

DEMONSTRATION_BANNER = (
    "DEMONSTRATION ONLY. MockInterpretationProvider did not call a language "
    "model and this is not an intelligent tarot reading."
)


class MockInterpretationProvider:
    provider_name = "mock"
    model_name = "mock-deterministic-v1"

    async def generate_reading(
        self,
        request: InterpretationRequest,
    ) -> GeneratedInterpretation:
        # Build the same prompt a real provider would send, so a prompt
        # regression fails here instead of only in a later integration.
        build_messages(request)
        card_lines = []
        interpretations: list[CardInterpretation] = []
        for card in request.cards:
            text = (
                f"{DEMONSTRATION_BANNER} {card.position_name}: {card.card_name} "
                f"is {card.orientation}. Seed meaning consulted: {card.general_meaning}"
            )
            card_lines.append(
                f"{card.position_name} = {card.card_name} ({card.orientation})"
            )
            interpretations.append(
                CardInterpretation(
                    position_index=card.position_index,
                    position_name=card.position_name,
                    card_name=card.card_name,
                    orientation=card.orientation,
                    interpretation=text,
                )
            )
        relationship = (
            f"{DEMONSTRATION_BANNER} Card order is fixed as: "
            + "; ".join(card_lines)
            + "."
        )
        structured = StructuredInterpretation(
            card_interpretations=interpretations,
            relationships=relationship,
            overall=(
                f"{DEMONSTRATION_BANNER} Spread {request.spread_name}. "
                f"Question: {request.question}"
            ),
            guidance=(
                f"{DEMONSTRATION_BANNER} Reflect on the symbols above for the "
                f"question {request.question!r}. This is not model advice."
            ),
            disclaimer=f"{DEMONSTRATION_BANNER} {SYMBOLIC_DISCLAIMER}",
        )
        return GeneratedInterpretation(
            provider=self.provider_name,
            model_name=self.model_name,
            interpretation_text=render_interpretation_text(structured),
            structured_result=structured,
        )
