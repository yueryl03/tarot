"""Random sources for shuffling.

Production readings use :class:`SystemRandomSource`, which draws from
``secrets.SystemRandom``. The other sources exist so tests can reproduce a
permutation. Nothing in the request path selects them.
"""

from secrets import SystemRandom
from typing import Protocol


class RandomSource(Protocol):
    """Uniform integer source used by Fisher-Yates and orientation assignment."""

    def randbelow(self, exclusive_upper: int) -> int:
        """Return a uniform integer in ``[0, exclusive_upper)``."""


class SystemRandomSource:
    """Cryptographic source backed by ``secrets.SystemRandom``.

    ``SystemRandom.randrange`` uses the operating system's generator and
    rejection sampling, so each index and each orientation bit is uniform.
    ``secrets.randbelow`` is the same implementation.
    """

    def __init__(self) -> None:
        self._rng = SystemRandom()

    def randbelow(self, exclusive_upper: int) -> int:
        if exclusive_upper <= 0:
            raise ValueError("exclusive_upper must be positive")
        return self._rng.randrange(exclusive_upper)


class SequenceRandomSource:
    """Plays back scripted integers. For tests only."""

    def __init__(self, values: list[int] | tuple[int, ...]) -> None:
        self._values = list(values)
        self._index = 0

    def randbelow(self, exclusive_upper: int) -> int:
        if exclusive_upper <= 0:
            raise ValueError("exclusive_upper must be positive")
        if self._index >= len(self._values):
            raise RuntimeError("SequenceRandomSource has no values left")
        value = self._values[self._index]
        self._index += 1
        if value < 0 or value >= exclusive_upper:
            raise ValueError(
                f"scripted value {value} is outside 0..{exclusive_upper - 1}"
            )
        return value

    @property
    def remaining(self) -> int:
        return len(self._values) - self._index


class XorShift32Source:
    """Deterministic 32-bit xorshift with rejection sampling. For tests only.

    This is not the production shuffle source. It exists so a test can rebuild
    the same deck from a seed and so the optional simulation can be repeated.
    """

    def __init__(self, seed: int) -> None:
        if seed == 0:
            raise ValueError("seed must be non-zero")
        self._state = seed & 0xFFFFFFFF

    def randbelow(self, exclusive_upper: int) -> int:
        if exclusive_upper <= 0:
            raise ValueError("exclusive_upper must be positive")
        if exclusive_upper == 1:
            return 0
        space = 1 << 32
        limit = space - (space % exclusive_upper)
        while True:
            value = self._next()
            if value < limit:
                return value % exclusive_upper

    def _next(self) -> int:
        state = self._state
        state ^= (state << 13) & 0xFFFFFFFF
        state ^= (state >> 17) & 0xFFFFFFFF
        state ^= (state << 5) & 0xFFFFFFFF
        self._state = state
        return state
