"""Framework-independent entry point for shuffling and draw planning.

The engine does not import FastAPI, SQLAlchemy, or an AI provider. A reading
service persists the deck this engine returns and never asks the engine to
shuffle that reading again.
"""

from collections.abc import Sequence

from app.domain.draw import PlannedDraw, plan_draw
from app.domain.enums import DrawMode
from app.domain.random_source import RandomSource
from app.domain.shuffle import ShuffledDeck, shuffle_deck


class TarotEngine:
    def __init__(self, rng: RandomSource) -> None:
        self.rng = rng

    def create_deck(
        self,
        card_ids: Sequence[int],
        *,
        reversals_enabled: bool,
    ) -> ShuffledDeck:
        return shuffle_deck(
            card_ids,
            self.rng,
            reversals_enabled=reversals_enabled,
        )

    def plan_draw(
        self,
        *,
        mode: DrawMode,
        count: int | None,
        slot_indices: Sequence[int] | None,
        revealed_slots: set[int],
        next_position_index: int,
        spread_card_count: int,
    ) -> tuple[PlannedDraw, ...]:
        return plan_draw(
            mode=mode,
            count=count,
            slot_indices=slot_indices,
            revealed_slots=revealed_slots,
            next_position_index=next_position_index,
            spread_card_count=spread_card_count,
        )
