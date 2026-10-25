"""The 78-card catalog. Orientation is not stored on this table."""

from sqlalchemy import CheckConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TarotCard(Base):
    __tablename__ = "tarot_cards"
    __table_args__ = (
        CheckConstraint(
            "arcana_type IN ('major', 'minor')",
            name="ck_tarot_cards_arcana_type",
        ),
        CheckConstraint(
            "suit IS NULL OR suit IN ('wands', 'cups', 'swords', 'pentacles')",
            name="ck_tarot_cards_suit",
        ),
        CheckConstraint(
            "(arcana_type = 'major' AND suit IS NULL) "
            "OR (arcana_type = 'minor' AND suit IS NOT NULL)",
            name="ck_tarot_cards_suit_matches_arcana",
        ),
        CheckConstraint(
            "canonical_number >= 0 AND canonical_number <= 77",
            name="ck_tarot_cards_canonical_number",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    arcana_type: Mapped[str] = mapped_column(String(16), nullable=False)
    suit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    rank: Mapped[str] = mapped_column(String(16), nullable=False)
    canonical_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_key: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True)

    meanings: Mapped[list["TarotMeaning"]] = relationship(
        back_populates="card",
        lazy="raise",
        order_by="TarotMeaning.orientation",
        cascade="all, delete-orphan",
    )
