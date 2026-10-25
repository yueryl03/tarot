"""Idealised physical shuffle.

This module models a careful shuffle of one 78-card deck:

* Fisher-Yates produces a uniform random permutation. Every card is equally
  likely to land in every slot, so before any card is revealed
  ``P(a specific card) = 1/78`` for the top of the deck and for any fixed slot.
* When reversals are enabled, each card's orientation is an independent fair
  coin flipped once while the deck is created:
  ``P(upright) = P(reversed) = 1/2``. Combined with the permutation,
  ``P(a specific card with a specified orientation) = 1/156`` for the first
  card. Orientation is stored with the slot and is never sampled again.
* When reversals are disabled, every card is upright and the orientation bit
  is not drawn.
* After ``k`` cards have been revealed, ``78 - k`` cards remain. The next top
  card is uniform among those remaining cards. Its orientation is the one
  stored at shuffle time.

This is an idealised model. A person shuffling physical cards does not
necessarily produce a perfectly uniform order or a perfectly fair rate of
reversals. The engine does not try to imitate hand bias, and it does not ask
a language model to pick cards.

The random source is injected. Production code passes
:class:`app.domain.random_source.SystemRandomSource`. The Python ``random``
module is intentionally not used.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.constants import DECK_SIZE
from app.domain.enums import Orientation
from app.domain.errors import TarotError
from app.domain.random_source import RandomSource


@dataclass(frozen=True, slots=True)
class DeckSlotPlan:
    """One face-down physical card in a newly shuffled deck."""

    slot_index: int
    card_id: int
    orientation: Orientation


@dataclass(frozen=True, slots=True)
class ShuffledDeck:
    """The full order and orientation of one reading, fixed at creation."""

    slots: tuple[DeckSlotPlan, ...]

    def __post_init__(self) -> None:
        indexes = [slot.slot_index for slot in self.slots]
        card_ids = [slot.card_id for slot in self.slots]
        if indexes != list(range(DECK_SIZE)):
            raise ValueError("A shuffled deck must contain slots 0 through 77.")
        if len(set(card_ids)) != DECK_SIZE:
            raise ValueError("A shuffled deck must contain each card once.")
        for slot in self.slots:
            if slot.orientation not in (Orientation.UPRIGHT, Orientation.REVERSED):
                raise ValueError("A deck slot has an invalid orientation.")

    @property
    def card_ids(self) -> tuple[int, ...]:
        return tuple(slot.card_id for slot in self.slots)


def fisher_yates(items: Sequence[int], rng: RandomSource) -> list[int]:
    """Return a new list shuffled with the modern Fisher-Yates algorithm.

    For ``i`` from ``n - 1`` down to ``1``, swap index ``i`` with a uniform
    index in ``0 .. i`` inclusive. The input sequence is not modified.
    """

    shuffled = list(items)
    for i in range(len(shuffled) - 1, 0, -1):
        j = rng.randbelow(i + 1)
        if j != i:
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    return shuffled


def choose_orientation(rng: RandomSource, *, reversals_enabled: bool) -> Orientation:
    """Assign one card's orientation.

    Reversals disabled: always upright, and the random source is not called.
    Reversals enabled: one independent ``randbelow(2)`` call. ``1`` is reversed.
    """

    if not reversals_enabled:
        return Orientation.UPRIGHT
    return Orientation.REVERSED if rng.randbelow(2) == 1 else Orientation.UPRIGHT


def shuffle_deck(
    card_ids: Sequence[int],
    rng: RandomSource,
    *,
    reversals_enabled: bool,
) -> ShuffledDeck:
    """Shuffle ``card_ids`` once into 78 oriented slots.

    ``card_ids`` must already be the complete catalog of 78 unique cards.
    The same card cannot appear twice, and orientation is not a second card.
    """

    if len(card_ids) != DECK_SIZE or len(set(card_ids)) != DECK_SIZE:
        raise TarotError(
            "A reading deck must be shuffled from exactly 78 unique cards.",
            code="deck_integrity",
            details={"card_count": len(card_ids), "unique_count": len(set(card_ids))},
        )
    ordered = fisher_yates(card_ids, rng)
    if len(ordered) != DECK_SIZE or len(set(ordered)) != DECK_SIZE:
        raise TarotError(
            "The shuffle did not produce a permutation of the deck.",
            code="deck_integrity",
        )
    slots = tuple(
        DeckSlotPlan(
            slot_index=index,
            card_id=card_id,
            orientation=choose_orientation(rng, reversals_enabled=reversals_enabled),
        )
        for index, card_id in enumerate(ordered)
    )
    return ShuffledDeck(slots)
