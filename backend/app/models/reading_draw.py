"""A revealed slot assigned to one spread position."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReadingDraw(Base):
    __tablename__ = "reading_draws"
    __table_args__ = (
        UniqueConstraint("deck_slot_id", name="uq_reading_draws_deck_slot"),
        UniqueConstraint(
            "reading_id",
            "spread_position_index",
            name="uq_reading_draws_reading_position",
        ),
        CheckConstraint(
            "spread_position_index >= 0",
            name="ck_reading_draws_position_nonnegative",
        ),
        ForeignKeyConstraint(
            ["reading_id", "deck_slot_id"],
            ["reading_deck_slots.reading_id", "reading_deck_slots.id"],
            name="fk_reading_draws_slot_same_reading",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    reading_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("reading_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    deck_slot_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    spread_position_index: Mapped[int] = mapped_column(Integer, nullable=False)
    revealed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
