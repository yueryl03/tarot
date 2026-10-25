"""Production shuffle boundary.

This service creates a new deck. It has no method that reshuffles a reading
that already exists. Callers persist the returned slots and reveal them later
without calling this service again.
"""

from collections.abc import Sequence

from app.domain.random_source import RandomSource, SystemRandomSource
from app.domain.shuffle import ShuffledDeck
from app.services.tarot_engine import TarotEngine


class ShuffleService:
    def __init__(self, rng: RandomSource | None = None) -> None:
        self.rng: RandomSource = rng if rng is not None else SystemRandomSource()
        self.engine = TarotEngine(self.rng)

    def shuffle_new_deck(
        self,
        card_ids: Sequence[int],
        *,
        reversals_enabled: bool,
    ) -> ShuffledDeck:
        return self.engine.create_deck(card_ids, reversals_enabled=reversals_enabled)
