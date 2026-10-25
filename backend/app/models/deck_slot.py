"""Persisted shuffled deck. One row is one physical card in one reading."""

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReadingDeckSlot(Base):
    """Immutable slot created with the reading.

    ``slot_index`` 0 is the top of the deck. ``orientation`` is chosen during
    the shuffle and must not be sampled again when the slot is revealed.
    """

    __tablename__ = "reading_deck_slots"
    __table_args__ = (
        UniqueConstraint(
            "reading_id",
            "slot_index",
            name="uq_reading_deck_slots_reading_slot",
        ),
        UniqueConstraint(
            "reading_id",
            "card_id",
            name="uq_reading_deck_slots_reading_card",
        ),
        UniqueConstraint(
            "reading_id",
            "id",
            name="uq_reading_deck_slots_reading_id_id",
        ),
        CheckConstraint(
            "slot_index >= 0 AND slot_index <= 77",
            name="ck_reading_deck_slots_slot_index",
        ),
        CheckConstraint(
            "orientation IN ('upright', 'reversed')",
            name="ck_reading_deck_slots_orientation",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    reading_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reading_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    card_id: Mapped[int] = mapped_column(
        ForeignKey("tarot_cards.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    slot_index: Mapped[int] = mapped_column(Integer, nullable=False)
    orientation: Mapped[str] = mapped_column(String(16), nullable=False)
