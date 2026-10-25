"""Replaceable upright and reversed meanings. One row per card per orientation."""

from sqlalchemy import CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.tarot_card import TarotCard


class TarotMeaning(Base):
    __tablename__ = "tarot_meanings"
    __table_args__ = (
        UniqueConstraint("card_id", "orientation", name="uq_tarot_meanings_card_orientation"),
        CheckConstraint(
            "orientation IN ('upright', 'reversed')",
            name="ck_tarot_meanings_orientation",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    card_id: Mapped[int] = mapped_column(
        ForeignKey("tarot_cards.id", ondelete="CASCADE"),
        nullable=False,
    )
    orientation: Mapped[str] = mapped_column(String(16), nullable=False)
    general_meaning: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    love_meaning: Mapped[str | None] = mapped_column(Text, nullable=True)
    career_meaning: Mapped[str | None] = mapped_column(Text, nullable=True)
    advice: Mapped[str | None] = mapped_column(Text, nullable=True)

    card: Mapped[TarotCard] = relationship(back_populates="meanings", lazy="raise")
