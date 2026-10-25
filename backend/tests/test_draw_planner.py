"""Draw planning has no random source and no partial plan."""

import pytest

from app.domain.draw import plan_draw
from app.domain.enums import DrawMode
from app.domain.errors import TarotError


def _plan(**kwargs):
    defaults = {
        "mode": DrawMode.TOP,
        "count": 1,
        "slot_indices": None,
        "revealed_slots": set(),
        "next_position_index": 0,
        "spread_card_count": 3,
    }
    defaults.update(kwargs)
    return plan_draw(**defaults)


def test_top_draw_takes_the_lowest_remaining_slots_in_order() -> None:
    plan = _plan(count=3)
    assert [(item.slot_index, item.spread_position_index) for item in plan] == [
        (0, 0),
        (1, 1),
        (2, 2),
    ]


def test_top_draw_skips_slots_that_were_selected_earlier() -> None:
    plan = _plan(
        count=2,
        revealed_slots={0, 2},
        next_position_index=2,
        spread_card_count=5,
    )
    assert [(item.slot_index, item.spread_position_index) for item in plan] == [
        (1, 2),
        (3, 3),
    ]


def test_select_preserves_the_requested_order() -> None:
    plan = _plan(
        mode=DrawMode.SELECT,
        count=None,
        slot_indices=[12, 40, 7],
        spread_card_count=5,
    )
    assert [(item.slot_index, item.spread_position_index) for item in plan] == [
        (12, 0),
        (40, 1),
        (7, 2),
    ]


def test_selecting_the_same_slot_twice_fails() -> None:
    with pytest.raises(TarotError) as caught:
        _plan(mode=DrawMode.SELECT, count=None, slot_indices=[4, 4], spread_card_count=5)
    assert caught.value.code == "duplicate_slots"


def test_invalid_slot_fails() -> None:
    with pytest.raises(TarotError) as caught:
        _plan(mode=DrawMode.SELECT, count=None, slot_indices=[12, 99])
    assert caught.value.code == "invalid_slot"
    with pytest.raises(TarotError) as negative:
        _plan(mode=DrawMode.SELECT, count=None, slot_indices=[-1])
    assert negative.value.code == "invalid_slot"


def test_drawing_more_than_the_spread_allows_fails() -> None:
    with pytest.raises(TarotError) as caught:
        _plan(count=4, spread_card_count=3)
    assert caught.value.code == "draw_exceeds_spread"
    with pytest.raises(TarotError) as selected:
        _plan(
            mode=DrawMode.SELECT,
            count=None,
            slot_indices=[0, 1, 2, 3],
            spread_card_count=3,
        )
    assert selected.value.code == "draw_exceeds_spread"


def test_drawing_after_the_spread_is_full_fails() -> None:
    with pytest.raises(TarotError) as caught:
        _plan(count=1, next_position_index=3, spread_card_count=3)
    assert caught.value.code == "reading_already_completed"


def test_already_revealed_slot_fails_without_a_partial_plan() -> None:
    with pytest.raises(TarotError) as caught:
        _plan(
            mode=DrawMode.SELECT,
            count=None,
            slot_indices=[5, 1],
            revealed_slots={1},
            spread_card_count=5,
        )
    assert caught.value.code == "slot_already_revealed"


def test_celtic_cross_limit_comes_from_the_argument() -> None:
    plan = _plan(count=10, spread_card_count=10)
    assert len(plan) == 10
    with pytest.raises(TarotError) as caught:
        _plan(count=11, spread_card_count=10)
    assert caught.value.code == "draw_exceeds_spread"


def test_single_card_spread_accepts_one_card() -> None:
    plan = _plan(count=1, spread_card_count=1)
    assert len(plan) == 1
    with pytest.raises(TarotError):
        _plan(count=2, spread_card_count=1)
