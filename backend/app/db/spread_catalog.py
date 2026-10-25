"""Database-defined spreads.

Adding a spread here and re-seeding is enough. The draw planner only reads
``card_count`` and assigns positions in reveal order.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SpreadPositionSpec:
    position_index: int
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class SpreadSpec:
    slug: str
    name: str
    description: str
    positions: tuple[SpreadPositionSpec, ...]

    @property
    def card_count(self) -> int:
        return len(self.positions)


def _positions(*rows: tuple[str, str]) -> tuple[SpreadPositionSpec, ...]:
    return tuple(
        SpreadPositionSpec(position_index=index, name=name, description=description)
        for index, (name, description) in enumerate(rows)
    )


SPREADS: tuple[SpreadSpec, ...] = (
    SpreadSpec(
        slug="single-card",
        name="Single Card",
        description="One card for a focused piece of guidance.",
        positions=_positions(
            (
                "Main guidance",
                "The central theme to reflect on for this question.",
            ),
        ),
    ),
    SpreadSpec(
        slug="past-present-future",
        name="Three Card Spread",
        description="A three-card timeline: what has shaped the matter, what is active now, and what is emerging.",
        positions=_positions(
            ("Past", "Influences that have already shaped the question."),
            ("Present", "The heart of the situation as it stands now."),
            ("Future", "The direction the situation is moving toward."),
        ),
    ),
    SpreadSpec(
        slug="five-card",
        name="Five Card Spread",
        description="Five cards covering the situation, the challenge, a hidden influence, advice, and a potential outcome.",
        positions=_positions(
            ("Current situation", "What is most active in the matter right now."),
            ("Challenge", "The friction or obstacle asking for attention."),
            ("Hidden influence", "Something working under the surface."),
            ("Advice", "A constructive way to meet the situation."),
            ("Potential outcome", "A possible result if the current course continues."),
        ),
    ),
    SpreadSpec(
        slug="celtic-cross",
        name="Celtic Cross",
        description=(
            "A ten-card Celtic Cross. Position order follows one common modern "
            "layout derived from the public-domain Rider-Waite tradition: present, "
            "challenge, foundation, recent past, crown, near future, self, "
            "environment, hopes and fears, and outcome. Other lineages number the "
            "staff differently."
        ),
        positions=_positions(
            ("Present", "The heart of the matter and the querent's current situation."),
            ("Challenge", "What crosses the present: the immediate dynamic or obstacle."),
            ("Foundation", "The root of the situation, including an older influence."),
            ("Recent past", "What is just leaving or has recently shaped the matter."),
            ("Crown", "A conscious aim, emerging potential, or the best that is hoped."),
            ("Near future", "What is approaching in the shorter term."),
            ("Self", "The querent's attitude and how they see themselves in this."),
            ("Environment", "Other people and the surrounding climate of the question."),
            ("Hopes and fears", "What the querent hopes for or fears will happen."),
            ("Outcome", "A likely culmination if the current course continues."),
        ),
    ),
)

REQUIRED_SPREAD_SLUGS = (
    "single-card",
    "past-present-future",
    "five-card",
    "celtic-cross",
)


def all_spreads() -> tuple[SpreadSpec, ...]:
    return SPREADS


def validate_spread_catalog(
    spreads: tuple[SpreadSpec, ...] | None = None,
) -> tuple[SpreadSpec, ...]:
    catalog = all_spreads() if spreads is None else spreads
    slugs = [spread.slug for spread in catalog]
    if len(slugs) != len(set(slugs)):
        raise ValueError("Spread slugs must be unique.")
    missing = [slug for slug in REQUIRED_SPREAD_SLUGS if slug not in slugs]
    if missing:
        raise ValueError(f"Missing required spreads: {', '.join(missing)}.")
    for spread in catalog:
        if spread.card_count < 1:
            raise ValueError(f"Spread {spread.slug} has no positions.")
        indexes = [position.position_index for position in spread.positions]
        if indexes != list(range(spread.card_count)):
            raise ValueError(
                f"Spread {spread.slug} positions must be contiguous from 0."
            )
        if any(not position.name.strip() for position in spread.positions):
            raise ValueError(f"Spread {spread.slug} has an empty position name.")
    by_slug = {spread.slug: spread for spread in catalog}
    if by_slug["past-present-future"].card_count != 3:
        raise ValueError("past-present-future must contain 3 positions.")
    if by_slug["celtic-cross"].card_count != 10:
        raise ValueError("celtic-cross must contain 10 positions.")
    return catalog
