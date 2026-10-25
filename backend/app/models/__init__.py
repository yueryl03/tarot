"""SQLAlchemy models. Importing this package registers every table."""

from app.models.base import Base
from app.models.deck_slot import ReadingDeckSlot
from app.models.idempotency import IdempotencyKey
from app.models.interpretation import Interpretation
from app.models.reading import ReadingSession
from app.models.reading_draw import ReadingDraw
from app.models.spread import TarotSpread, TarotSpreadPosition
from app.models.tarot_card import TarotCard
from app.models.tarot_meaning import TarotMeaning

__all__ = [
    "Base",
    "IdempotencyKey",
    "Interpretation",
    "ReadingDeckSlot",
    "ReadingDraw",
    "ReadingSession",
    "TarotCard",
    "TarotMeaning",
    "TarotSpread",
    "TarotSpreadPosition",
]
