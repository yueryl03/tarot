"""Shuffle correctness. Production randomness is secrets.SystemRandom."""

import ast
from pathlib import Path

import pytest

from app.domain.constants import DECK_SIZE
from app.domain.enums import Orientation
from app.domain.errors import TarotError
from app.domain.random_source import (
    SequenceRandomSource,
    SystemRandomSource,
    XorShift32Source,
)
from app.domain.shuffle import fisher_yates, shuffle_deck
from app.services.shuffle_service import ShuffleService
from app.services.tarot_engine import TarotEngine

CARD_IDS = list(range(1, DECK_SIZE + 1))


def test_application_does_not_import_the_random_module() -> None:
    root = Path(__file__).resolve().parents[1] / "app"
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                assert name != "random" and not name.startswith("random."), path


def test_fisher_yates_follows_the_scripted_swaps() -> None:
    # i=3 j=2, i=2 j=0, i=1 j=1
    shuffled = fisher_yates([10, 20, 30, 40], SequenceRandomSource([2, 0, 1]))
    assert shuffled == [40, 20, 10, 30]


def test_fisher_yates_does_not_mutate_the_input() -> None:
    items = [1, 2, 3, 4]
    fisher_yates(items, SequenceRandomSource([0, 0, 0]))
    assert items == [1, 2, 3, 4]


def test_every_deck_contains_78_unique_cards() -> None:
    deck = TarotEngine(XorShift32Source(99)).create_deck(
        CARD_IDS,
        reversals_enabled=True,
    )
    assert len(deck.slots) == DECK_SIZE
    assert [slot.slot_index for slot in deck.slots] == list(range(DECK_SIZE))
    assert sorted(deck.card_ids) == CARD_IDS
    assert len(set(deck.card_ids)) == DECK_SIZE


def test_shuffle_is_a_permutation_for_many_system_random_decks() -> None:
    engine = TarotEngine(SystemRandomSource())
    for _ in range(20):
        deck = engine.create_deck(CARD_IDS, reversals_enabled=True)
        assert sorted(deck.card_ids) == CARD_IDS
        assert all(
            slot.orientation in (Orientation.UPRIGHT, Orientation.REVERSED)
            for slot in deck.slots
        )


def test_reversals_disabled_are_upright_and_do_not_draw_orientation_bits() -> None:
    class Counting:
        def __init__(self) -> None:
            self.calls = 0
            self.inner = XorShift32Source(5)

        def randbelow(self, exclusive_upper: int) -> int:
            self.calls += 1
            return self.inner.randbelow(exclusive_upper)

    rng = Counting()
    deck = shuffle_deck(CARD_IDS, rng, reversals_enabled=False)
    assert rng.calls == DECK_SIZE - 1
    assert {slot.orientation for slot in deck.slots} == {Orientation.UPRIGHT}


def test_orientations_are_independent_of_card_identity() -> None:
    script = [0] * (DECK_SIZE - 1) + [1, 0] * (DECK_SIZE // 2)
    first = shuffle_deck(CARD_IDS, SequenceRandomSource(script), reversals_enabled=True)
    second = shuffle_deck(
        CARD_IDS,
        SequenceRandomSource(script),
        reversals_enabled=True,
    )
    assert [slot.orientation for slot in first.slots] == (
        [Orientation.REVERSED, Orientation.UPRIGHT] * (DECK_SIZE // 2)
    )
    assert first.card_ids == second.card_ids
    flipped = shuffle_deck(
        CARD_IDS,
        SequenceRandomSource([0] * (DECK_SIZE - 1) + [0, 1] * (DECK_SIZE // 2)),
        reversals_enabled=True,
    )
    assert flipped.card_ids == first.card_ids
    assert flipped.slots[0].orientation is Orientation.UPRIGHT
    assert first.slots[0].orientation is Orientation.REVERSED


def test_same_seed_rebuilds_the_same_deck_and_another_seed_does_not() -> None:
    left = TarotEngine(XorShift32Source(42)).create_deck(CARD_IDS, reversals_enabled=True)
    right = TarotEngine(XorShift32Source(42)).create_deck(CARD_IDS, reversals_enabled=True)
    other = TarotEngine(XorShift32Source(43)).create_deck(CARD_IDS, reversals_enabled=True)
    assert left == right
    assert left != other


def test_incomplete_catalog_is_rejected() -> None:
    with pytest.raises(TarotError) as caught:
        shuffle_deck([1, 2, 3], SystemRandomSource(), reversals_enabled=True)
    assert caught.value.code == "deck_integrity"


def test_duplicate_catalog_is_rejected() -> None:
    ids = CARD_IDS.copy()
    ids[-1] = ids[0]
    with pytest.raises(TarotError) as caught:
        shuffle_deck(ids, SystemRandomSource(), reversals_enabled=False)
    assert caught.value.code == "deck_integrity"


def test_default_shuffle_service_uses_system_random() -> None:
    service = ShuffleService()
    assert isinstance(service.rng, SystemRandomSource)


def test_separate_engines_are_independent() -> None:
    decks = [
        tuple(
            TarotEngine(SystemRandomSource())
            .create_deck(CARD_IDS, reversals_enabled=True)
            .card_ids
        )
        for _ in range(5)
    ]
    assert len(set(decks)) > 1
