"""Optional frequency report for the production shuffle.

Ordinary tests do not depend on exact frequencies. Run this module directly,
or ``pytest -m statistical``, when you want a larger sample.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

from app.domain.constants import DECK_SIZE
from app.domain.enums import Orientation
from app.domain.random_source import RandomSource, SystemRandomSource, XorShift32Source
from app.domain.shuffle import shuffle_deck

CARD_IDS = list(range(1, DECK_SIZE + 1))


@dataclass(frozen=True, slots=True)
class SimulationReport:
    shuffles: int
    reversals_enabled: bool
    first_position_counts: dict[int, int]
    upright_count: int
    reversed_count: int
    reversed_per_reading_mean: float
    max_first_position_z: float
    orientation_z: float

    @property
    def within_tolerance(self) -> bool:
        if not self.reversals_enabled:
            return self.reversed_count == 0 and self.upright_count == self.shuffles * DECK_SIZE
        return (
            self.max_first_position_z <= 6
            and abs(self.orientation_z) <= 6
            and abs(self.reversed_per_reading_mean - (DECK_SIZE / 2)) <= 2
        )


def simulate(
    shuffles: int,
    *,
    reversals_enabled: bool = True,
    rng: RandomSource | None = None,
) -> SimulationReport:
    """Shuffle many full decks and summarise the first slot and orientations."""

    source = rng or SystemRandomSource()
    first_counts = {card_id: 0 for card_id in CARD_IDS}
    upright = 0
    reversed_count = 0
    reversed_per_reading = 0
    for _ in range(shuffles):
        deck = shuffle_deck(CARD_IDS, source, reversals_enabled=reversals_enabled)
        if sorted(deck.card_ids) != CARD_IDS:
            raise RuntimeError("simulation produced a deck that is not a permutation")
        first_counts[deck.slots[0].card_id] += 1
        reversed_here = 0
        for slot in deck.slots:
            if slot.orientation is Orientation.UPRIGHT:
                upright += 1
            elif slot.orientation is Orientation.REVERSED:
                reversed_count += 1
                reversed_here += 1
            else:
                raise RuntimeError("invalid orientation")
        reversed_per_reading += reversed_here
    expected = shuffles / DECK_SIZE
    sigma = math.sqrt(shuffles * (1 / DECK_SIZE) * (1 - 1 / DECK_SIZE))
    max_z = max(abs(count - expected) / sigma for count in first_counts.values())
    total_orientations = upright + reversed_count
    orientation_sigma = math.sqrt(total_orientations * 0.25) if total_orientations else 1
    orientation_z = (upright - total_orientations / 2) / orientation_sigma
    return SimulationReport(
        shuffles=shuffles,
        reversals_enabled=reversals_enabled,
        first_position_counts=first_counts,
        upright_count=upright,
        reversed_count=reversed_count,
        reversed_per_reading_mean=reversed_per_reading / shuffles,
        max_first_position_z=max_z,
        orientation_z=orientation_z,
    )


def render_report(report: SimulationReport) -> str:
    lines = [
        "Idealised Fisher-Yates shuffle with independent fair orientations.",
        "This is not a model of human shuffle bias.",
        f"shuffles={report.shuffles} reversals_enabled={report.reversals_enabled}",
        (
            f"first-position max |z|={report.max_first_position_z:.3f} "
            f"(expected count {report.shuffles / DECK_SIZE:.2f})"
        ),
        (
            f"upright={report.upright_count} reversed={report.reversed_count} "
            f"orientation z={report.orientation_z:.3f}"
        ),
        f"mean reversed cards per reading={report.reversed_per_reading_mean:.3f}",
        f"within_tolerance={report.within_tolerance}",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Report shuffle and orientation frequencies.")
    parser.add_argument("--shuffles", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--no-reversals", action="store_true")
    args = parser.parse_args()
    rng = XorShift32Source(args.seed) if args.seed is not None else SystemRandomSource()
    report = simulate(
        args.shuffles,
        reversals_enabled=not args.no_reversals,
        rng=rng,
    )
    print(render_report(report))
    if not report.within_tolerance:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
