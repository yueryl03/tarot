"""Shared enumerations for cards, readings, and draws."""

from enum import Enum


class ArcanaType(str, Enum):
    MAJOR = "major"
    MINOR = "minor"


class Suit(str, Enum):
    WANDS = "wands"
    CUPS = "cups"
    SWORDS = "swords"
    PENTACLES = "pentacles"


class Orientation(str, Enum):
    UPRIGHT = "upright"
    REVERSED = "reversed"


class ReadingStatus(str, Enum):
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class DrawMode(str, Enum):
    TOP = "top"
    SELECT = "select"
