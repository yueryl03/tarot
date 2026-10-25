"""The 78-card Rider-Waite-Smith catalog and replaceable seed meanings.

Major Arcana use the Rider-Waite-Smith numbering (Strength 8, Justice 11).
Minor Arcana follow Wands, Cups, Swords, Pentacles, each from Ace to King.

Meanings are original development seed text generated from a small keyword
table. They are not copied from a licensed deck book and are not presented as
an authoritative tradition. Replace :func:`meanings_for` or the rows in
``tarot_meanings`` when a curated dataset is ready. Card identity does not
depend on that text.

``canonical_number`` is the stable deck index 0 through 77. Major cards use
their traditional numbers. Minor cards continue from 22.
"""

from dataclasses import dataclass

from app.domain.constants import DECK_SIZE

SEED_MEANING_PREFIX = (
    "Development seed meaning, not a licensed or proprietary source:"
)

_MAJOR_ROWS: tuple[tuple[int, str, str, tuple[str, ...], tuple[str, ...]], ...] = (
    (
        0,
        "The Fool",
        "A traveller steps toward an open cliff with a small pack and a white rose, an image of a beginning taken on trust.",
        ("beginnings", "spontaneity", "trust", "openness"),
        ("recklessness", "hesitation", "naivety", "mistimed start"),
    ),
    (
        1,
        "The Magician",
        "A figure stands at an altar holding the four suit tools, one hand raised and one pointing to the ground.",
        ("will", "skill", "focus", "resourcefulness"),
        ("manipulation", "scattered energy", "unused talent", "trickery"),
    ),
    (
        2,
        "The High Priestess",
        "A seated figure between a dark and a light pillar holds a scroll, with a veil behind her.",
        ("intuition", "mystery", "inner knowledge", "patience"),
        ("secrecy", "disconnection", "ignored instinct", "blocked insight"),
    ),
    (
        3,
        "The Empress",
        "A crowned figure rests in a fertile landscape, suggesting nurture, abundance, and creative growth.",
        ("abundance", "nurture", "creativity", "sensuality"),
        ("dependence", "smothering", "creative block", "neglect"),
    ),
    (
        4,
        "The Emperor",
        "A crowned figure sits on a stone throne marked with ram heads, an image of structure and authority.",
        ("structure", "authority", "stability", "leadership"),
        ("rigidity", "domination", "weak boundaries", "inflexibility"),
    ),
    (
        5,
        "The Hierophant",
        "A teacher seated between two pillars blesses two students, suggesting tradition and instruction.",
        ("tradition", "teaching", "belief", "mentorship"),
        ("dogma", "rebellion", "empty ritual", "questioned authority"),
    ),
    (
        6,
        "The Lovers",
        "Two figures stand beneath an angel, an image of a choice that joins values and relationship.",
        ("choice", "alignment", "relationship", "values"),
        ("disharmony", "avoided choice", "misalignment", "divided loyalty"),
    ),
    (
        7,
        "The Chariot",
        "An armoured figure rides a chariot drawn by a black sphinx and a white sphinx.",
        ("determination", "direction", "willpower", "momentum"),
        ("loss of control", "aggression", "stalled progress", "scattered drive"),
    ),
    (
        8,
        "Strength",
        "A calm figure gently closes a lion's jaws, suggesting courage that does not rely on force.",
        ("courage", "patience", "compassion", "inner power"),
        ("self-doubt", "force", "raw impulse", "depleted courage"),
    ),
    (
        9,
        "The Hermit",
        "A cloaked figure holds a lantern on a high path, an image of searching apart from the crowd.",
        ("solitude", "guidance", "reflection", "inner search"),
        ("isolation", "withdrawal", "refused guidance", "loneliness"),
    ),
    (
        10,
        "Wheel of Fortune",
        "A great wheel turns among symbolic figures, suggesting cycles and a change of circumstance.",
        ("cycles", "turning point", "change", "fortune"),
        ("resistance to change", "setback", "repeating pattern", "missed timing"),
    ),
    (
        11,
        "Justice",
        "A seated figure holds a sword and scales, an image of weighing a matter with clarity.",
        ("fairness", "truth", "accountability", "balance"),
        ("bias", "dishonesty", "avoided consequences", "unfairness"),
    ),
    (
        12,
        "The Hanged Man",
        "A figure hangs calmly by one foot from a living tree, seeing the matter from another angle.",
        ("pause", "surrender", "new perspective", "suspension"),
        ("stalling", "martyrdom", "refusal to let go", "needless delay"),
    ),
    (
        13,
        "Death",
        "A skeletal rider carries a banner while figures meet an ending that makes room for change.",
        ("ending", "transformation", "release", "transition"),
        ("resistance", "stagnation", "fear of change", "incomplete ending"),
    ),
    (
        14,
        "Temperance",
        "An angel pours liquid between two cups, with one foot in water and one on land.",
        ("balance", "moderation", "integration", "healing"),
        ("excess", "imbalance", "impatience", "conflicted parts"),
    ),
    (
        15,
        "The Devil",
        "A horned figure stands over two loosely chained people, an image of attachment and shadow.",
        ("attachment", "shadow", "bondage", "temptation"),
        ("release", "facing the shadow", "reclaimed power", "breaking a pattern"),
    ),
    (
        16,
        "The Tower",
        "Lightning strikes a crown from a tower and figures fall, an image of sudden revelation.",
        ("upheaval", "revelation", "collapse", "sudden change"),
        ("delayed upheaval", "fear of collapse", "avoided truth", "aftershock"),
    ),
    (
        17,
        "The Star",
        "A figure pours water under a great star, one stream onto land and one into a pool.",
        ("hope", "healing", "inspiration", "renewal"),
        ("discouragement", "doubt", "dimmed hope", "disconnection from faith"),
    ),
    (
        18,
        "The Moon",
        "Moonlight falls on a path between two towers, with a dog, a wolf, and a creature from the water.",
        ("uncertainty", "dreams", "illusion", "the unconscious"),
        ("clarity returning", "confusion", "anxiety", "revealed illusion"),
    ),
    (
        19,
        "The Sun",
        "A child rides a white horse beneath a bright sun, with sunflowers standing behind.",
        ("vitality", "clarity", "joy", "success"),
        ("dimmed joy", "temporary cloud", "overexposure", "delayed clarity"),
    ),
    (
        20,
        "Judgement",
        "Figures rise as a trumpet sounds from the sky, an image of awakening and reckoning.",
        ("awakening", "reckoning", "calling", "forgiveness"),
        ("self-judgement", "ignored calling", "unresolved past", "refusal to answer"),
    ),
    (
        21,
        "The World",
        "A dancer turns inside a wreath, with a figure in each corner, an image of completion.",
        ("completion", "wholeness", "integration", "arrival"),
        ("unfinished business", "loose ends", "delayed completion", "seeking closure"),
    ),
)

_RANKS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("ace", "Ace", ("seed", "beginning", "raw potential")),
    ("2", "2", ("duality", "planning", "partnership")),
    ("3", "3", ("growth", "expression", "first results")),
    ("4", "4", ("stability", "structure", "pause")),
    ("5", "5", ("conflict", "instability", "challenge")),
    ("6", "6", ("recovery", "passage", "harmony")),
    ("7", "7", ("assessment", "perseverance", "strategy")),
    ("8", "8", ("movement", "mastery", "momentum")),
    ("9", "9", ("culmination", "intensity", "near completion")),
    ("10", "10", ("completion", "legacy", "full cycle")),
    ("page", "Page", ("study", "message", "curiosity")),
    ("knight", "Knight", ("pursuit", "motion", "commitment")),
    ("queen", "Queen", ("inward mastery", "receptivity", "care")),
    ("king", "King", ("outward authority", "responsibility", "command")),
)

_SUITS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("wands", "Wands", ("will", "creativity", "enterprise")),
    ("cups", "Cups", ("emotion", "relationship", "intuition")),
    ("swords", "Swords", ("intellect", "conflict", "truth")),
    ("pentacles", "Pentacles", ("material world", "work", "body")),
)


@dataclass(frozen=True, slots=True)
class CardSpec:
    canonical_number: int
    name: str
    arcana_type: str
    suit: str | None
    rank: str
    description: str
    image_key: str
    upright_keywords: tuple[str, ...]
    reversed_keywords: tuple[str, ...]

    @property
    def id(self) -> int:
        return self.canonical_number + 1


@dataclass(frozen=True, slots=True)
class MeaningSpec:
    orientation: str
    general_meaning: str
    keywords: tuple[str, ...]
    love_meaning: str
    career_meaning: str
    advice: str


def _slug(name: str) -> str:
    return name.lower().replace(" ", "-")


def _majors() -> list[CardSpec]:
    cards: list[CardSpec] = []
    for number, name, description, upright, reversed_words in _MAJOR_ROWS:
        cards.append(
            CardSpec(
                canonical_number=number,
                name=name,
                arcana_type="major",
                suit=None,
                rank=str(number),
                description=description,
                image_key=f"rws/major/{number:02d}-{_slug(name)}",
                upright_keywords=upright,
                reversed_keywords=reversed_words,
            )
        )
    return cards


def _minors() -> list[CardSpec]:
    cards: list[CardSpec] = []
    for suit_index, (suit, suit_name, suit_keywords) in enumerate(_SUITS):
        for rank_index, (rank, rank_label, rank_keywords) in enumerate(_RANKS):
            canonical = 22 + suit_index * 14 + rank_index
            name = f"{rank_label} of {suit_name}"
            upright = rank_keywords + suit_keywords
            reversed_words = (
                f"delayed {rank_keywords[0]}",
                f"distorted {suit_keywords[0]}",
                "turning inward",
            )
            description = (
                f"Development seed description: the {name} expresses "
                f"{rank_keywords[0]} through the {suit_name} themes of "
                f"{', '.join(suit_keywords)}."
            )
            cards.append(
                CardSpec(
                    canonical_number=canonical,
                    name=name,
                    arcana_type="minor",
                    suit=suit,
                    rank=rank,
                    description=description,
                    image_key=f"rws/{suit}/{rank}",
                    upright_keywords=upright,
                    reversed_keywords=reversed_words,
                )
            )
    return cards


def all_cards() -> tuple[CardSpec, ...]:
    return tuple(_majors() + _minors())


def meanings_for(card: CardSpec) -> tuple[MeaningSpec, MeaningSpec]:
    """Build the two replaceable meaning rows for one card."""

    return (
        _meaning(card, "upright", card.upright_keywords),
        _meaning(card, "reversed", card.reversed_keywords),
    )


def _meaning(card: CardSpec, orientation: str, keywords: tuple[str, ...]) -> MeaningSpec:
    joined = ", ".join(keywords)
    prefix = SEED_MEANING_PREFIX
    return MeaningSpec(
        orientation=orientation,
        keywords=keywords,
        general_meaning=(
            f"{prefix} {card.name} {orientation} is associated with {joined}."
        ),
        love_meaning=(
            f"{prefix} in a relationship context, {card.name} {orientation} "
            f"echoes {joined}."
        ),
        career_meaning=(
            f"{prefix} in a work or material context, {card.name} {orientation} "
            f"echoes {joined}."
        ),
        advice=(
            f"Development seed advice: treat {card.name} {orientation} as a "
            f"symbol of {joined}. This is reflective, not a prediction."
        ),
    )


def validate_card_catalog(cards: tuple[CardSpec, ...] | None = None) -> tuple[CardSpec, ...]:
    """Raise ``ValueError`` if the catalog is not a complete 78-card deck."""

    catalog = all_cards() if cards is None else cards
    if len(catalog) != DECK_SIZE:
        raise ValueError(f"Expected {DECK_SIZE} cards, found {len(catalog)}.")
    numbers = [card.canonical_number for card in catalog]
    names = [card.name for card in catalog]
    image_keys = [card.image_key for card in catalog]
    if numbers != list(range(DECK_SIZE)):
        raise ValueError("canonical_number must be exactly 0 through 77 in order.")
    if len(set(names)) != DECK_SIZE:
        raise ValueError("Card names must be unique.")
    if len(set(image_keys)) != DECK_SIZE:
        raise ValueError("image_key values must be unique.")
    majors = [card for card in catalog if card.arcana_type == "major"]
    minors = [card for card in catalog if card.arcana_type == "minor"]
    if len(majors) != 22 or len(minors) != 56:
        raise ValueError("The deck must contain 22 major and 56 minor cards.")
    if any(card.suit is not None for card in majors):
        raise ValueError("Major arcana must not have a suit.")
    if any(card.suit is None for card in minors):
        raise ValueError("Minor arcana must have a suit.")
    for suit, _, _ in _SUITS:
        suited = [card for card in minors if card.suit == suit]
        if len(suited) != 14:
            raise ValueError(f"Suit {suit} must contain 14 cards.")
        ranks = [card.rank for card in suited]
        if ranks != [rank for rank, _, _ in _RANKS]:
            raise ValueError(f"Suit {suit} has an unexpected rank order.")
    if majors[8].name != "Strength" or majors[11].name != "Justice":
        raise ValueError("Major numbering must follow Rider-Waite-Smith.")
    for card in catalog:
        if not card.upright_keywords or not card.reversed_keywords:
            raise ValueError(f"{card.name} is missing keywords.")
        for meaning in meanings_for(card):
            if SEED_MEANING_PREFIX not in meaning.general_meaning:
                raise ValueError(f"{card.name} meaning is missing the seed prefix.")
            if not meaning.keywords:
                raise ValueError(f"{card.name} meaning has no keywords.")
    return catalog
