"""Catalog invariants that do not need a database."""

from app.db.card_catalog import SEED_MEANING_PREFIX, all_cards, meanings_for, validate_card_catalog
from app.db.spread_catalog import all_spreads, validate_spread_catalog
from app.domain.constants import DECK_SIZE


def test_catalog_is_a_78_card_rider_waite_smith_deck() -> None:
    cards = validate_card_catalog()
    assert len(cards) == DECK_SIZE
    assert len({card.name for card in cards}) == DECK_SIZE
    assert [card.canonical_number for card in cards] == list(range(DECK_SIZE))
    majors = [card for card in cards if card.arcana_type == "major"]
    assert len(majors) == 22
    assert majors[0].name == "The Fool"
    assert majors[8].name == "Strength"
    assert majors[11].name == "Justice"
    assert majors[21].name == "The World"
    minors = [card for card in cards if card.arcana_type == "minor"]
    assert len(minors) == 56
    for suit in ("wands", "cups", "swords", "pentacles"):
        assert len([card for card in minors if card.suit == suit]) == 14
    assert cards[22].name == "Ace of Wands"
    assert cards[77].name == "King of Pentacles"


def test_seed_meanings_are_labelled_and_cover_both_orientations() -> None:
    for card in all_cards():
        meanings = meanings_for(card)
        assert [meaning.orientation for meaning in meanings] == ["upright", "reversed"]
        for meaning in meanings:
            assert SEED_MEANING_PREFIX in meaning.general_meaning
            assert "licensed deck" not in meaning.general_meaning.lower()
            assert meaning.love_meaning
            assert meaning.career_meaning
            assert meaning.advice
            assert meaning.keywords


def test_required_spreads_are_data_not_draw_constants() -> None:
    spreads = {spread.slug: spread for spread in validate_spread_catalog()}
    assert spreads["single-card"].card_count == 1
    assert [item.name for item in spreads["past-present-future"].positions] == [
        "Past",
        "Present",
        "Future",
    ]
    assert spreads["five-card"].card_count == 5
    assert spreads["celtic-cross"].card_count == 10
    assert sum(spread.card_count for spread in all_spreads()) == 19
