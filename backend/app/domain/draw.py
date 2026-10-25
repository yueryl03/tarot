"""Plan which face-down slots a draw will reveal.

The planner has no random source and no database handle. It only checks the
request against the slots already revealed and the spread size. Callers must
apply the plan inside a transaction. A raised error means the plan is empty:
no slot should be consumed.
"""

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.constants import DECK_SIZE
from app.domain.enums import DrawMode
from app.domain.errors import TarotError


@dataclass(frozen=True, slots=True)
class PlannedDraw:
    slot_index: int
    spread_position_index: int


def plan_draw(
    *,
    mode: DrawMode,
    count: int | None,
    slot_indices: Sequence[int] | None,
    revealed_slots: set[int],
    next_position_index: int,
    spread_card_count: int,
    deck_size: int = DECK_SIZE,
) -> tuple[PlannedDraw, ...]:
    """Choose slots and the spread positions they will fill.

    Positions are assigned in reveal order. The first card of this request
    receives ``next_position_index``, which is the number of cards already
    revealed. Mode ``top`` takes the lowest remaining slot indexes: slot 0 is
    the top of the stored deck. Mode ``select`` keeps the caller's order.
    """

    if spread_card_count < 1:
        raise TarotError(
            "The selected spread has no positions.",
            code="spread_integrity",
        )
    remaining_positions = spread_card_count - next_position_index
    if remaining_positions <= 0 or next_position_index >= spread_card_count:
        raise TarotError(
            "This reading is already complete.",
            code="reading_already_completed",
            details={"spread_card_count": spread_card_count},
        )

    if mode is DrawMode.TOP:
        chosen = _from_top(
            count=count,
            revealed_slots=revealed_slots,
            deck_size=deck_size,
            remaining_positions=remaining_positions,
        )
    elif mode is DrawMode.SELECT:
        chosen = _from_selection(
            slot_indices=slot_indices,
            revealed_slots=revealed_slots,
            deck_size=deck_size,
            remaining_positions=remaining_positions,
        )
    else:
        raise TarotError("Unsupported draw mode.", code="invalid_draw")

    return tuple(
        PlannedDraw(
            slot_index=slot_index,
            spread_position_index=next_position_index + offset,
        )
        for offset, slot_index in enumerate(chosen)
    )


def _from_top(
    *,
    count: int | None,
    revealed_slots: set[int],
    deck_size: int,
    remaining_positions: int,
) -> list[int]:
    if count is None or count < 1:
        raise TarotError(
            "count must be at least 1 when drawing from the top.",
            code="invalid_draw",
        )
    if count > remaining_positions:
        raise TarotError(
            "The request draws more cards than the spread has left.",
            code="draw_exceeds_spread",
            details={
                "requested": count,
                "remaining_positions": remaining_positions,
            },
        )
    available = [slot for slot in range(deck_size) if slot not in revealed_slots]
    if count > len(available):
        raise TarotError(
            "The request draws more cards than the deck has left.",
            code="draw_exceeds_deck",
            details={"requested": count, "remaining_cards": len(available)},
        )
    return available[:count]


def _from_selection(
    *,
    slot_indices: Sequence[int] | None,
    revealed_slots: set[int],
    deck_size: int,
    remaining_positions: int,
) -> list[int]:
    if not slot_indices:
        raise TarotError(
            "slot_indices is required when selecting face-down cards.",
            code="invalid_draw",
        )
    selected = list(slot_indices)
    invalid = [slot for slot in selected if slot < 0 or slot >= deck_size]
    if invalid:
        raise TarotError(
            "One or more slot indexes are outside the deck.",
            code="invalid_slot",
            details={"slot_indices": invalid, "deck_size": deck_size},
        )
    if len(selected) != len(set(selected)):
        raise TarotError(
            "The same slot was selected more than once in this request.",
            code="duplicate_slots",
            details={"slot_indices": selected},
        )
    if len(selected) > remaining_positions:
        raise TarotError(
            "The request draws more cards than the spread has left.",
            code="draw_exceeds_spread",
            details={
                "requested": len(selected),
                "remaining_positions": remaining_positions,
            },
        )
    already = [slot for slot in selected if slot in revealed_slots]
    if already:
        raise TarotError(
            "One or more selected slots have already been revealed.",
            code="slot_already_revealed",
            details={"slot_indices": already},
        )
    return selected
