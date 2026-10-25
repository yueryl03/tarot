"""Simulation smoke test, plus an optional frequency check."""

import pytest

from app.domain.random_source import XorShift32Source
from scripts.shuffle_simulation import simulate


def test_simulation_smoke_uses_the_real_shuffle_function() -> None:
    report = simulate(30, reversals_enabled=True, rng=XorShift32Source(12345))
    assert sum(report.first_position_counts.values()) == 30
    assert report.upright_count + report.reversed_count == 30 * 78
    assert 0 <= report.reversed_per_reading_mean <= 78


@pytest.mark.statistical
def test_shuffle_frequencies_within_tolerance() -> None:
    report = simulate(4000, reversals_enabled=True)
    assert report.within_tolerance, report
