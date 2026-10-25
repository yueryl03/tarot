"""Prompt text for a future language-model provider.

The shuffle never uses this module. The prompt tells the model that the cards
are already chosen and that the reply is symbolic rather than factual.
"""

from app.ai.base import InterpretationRequest
from app.domain.interpretation import SYMBOLIC_DISCLAIMER


class PromptMessages:
    def __init__(self, system: str, user: str) -> None:
        self.system = system
        self.user = user

    def as_chat(self) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self.system},
            {"role": "user", "content": self.user},
        ]


def build_messages(request: InterpretationRequest) -> PromptMessages:
    system = "\n".join(
        [
            "You interpret tarot readings that have already been shuffled and drawn.",
            "You must not change, replace, reorder, or re-orient any card.",
            "You must not claim a different card was drawn.",
            SYMBOLIC_DISCLAIMER,
            "Do not present the reading as a verified prediction or as knowledge of another person's private thoughts.",
            "Respond with a single JSON object and no markdown.",
            "The JSON object must contain:",
            "card_interpretations: a list with one object per revealed card, in the given order,",
            "each with position_index, position_name, card_name, orientation, and interpretation;",
            "relationships: a string about how the cards sit together;",
            "overall: a string for the reading as a whole;",
            "guidance: a reflective suggestion, not a command about another person;",
            "disclaimer: a string that includes the symbolic limitation above.",
            "Use only the cards, orientations, positions, and meanings supplied in the user message.",
        ]
    )
    lines = [
        f"Question: {request.question}",
        f"Spread: {request.spread_name}",
        f"Spread description: {request.spread_description}",
        "Revealed cards, in draw order:",
    ]
    for card in request.cards:
        keywords = ", ".join(card.keywords) if card.keywords else "(none)"
        lines.extend(
            [
                (
                    f"- position_index={card.position_index}; "
                    f"position_name={card.position_name}; "
                    f"position_description={card.position_description}"
                ),
                (
                    f"  card_id={card.card_id}; card_name={card.card_name}; "
                    f"arcana_type={card.arcana_type}; suit={card.suit or ''}; "
                    f"rank={card.rank}; orientation={card.orientation}"
                ),
                f"  keywords: {keywords}",
                f"  general_meaning: {card.general_meaning}",
                f"  love_meaning: {card.love_meaning or ''}",
                f"  career_meaning: {card.career_meaning or ''}",
                f"  advice: {card.advice or ''}",
            ]
        )
    return PromptMessages(system=system, user="\n".join(lines))
