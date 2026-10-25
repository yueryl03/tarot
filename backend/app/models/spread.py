"""Spreads and the named positions inside them."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TarotSpread(Base):
    __tablename__ = "tarot_spreads"
    __table_args__ = (
        CheckConstraint("card_count > 0", name="ck_tarot_spreads_card_count"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    card_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    positions: Mapped[list["TarotSpreadPosition"]] = relationship(
        back_populates="spread",
        lazy="raise",
        order_by="TarotSpreadPosition.position_index",
        cascade="all, delete-orphan",
    )


class TarotSpreadPosition(Base):
    __tablename__ = "tarot_spread_positions"
    __table_args__ = (
        UniqueConstraint(
            "spread_id",
            "position_index",
            name="uq_tarot_spread_positions_spread_index",
        ),
        CheckConstraint(
            "position_index >= 0",
            name="ck_tarot_spread_positions_index",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    spread_id: Mapped[int] = mapped_column(
        ForeignKey("tarot_spreads.id", ondelete="CASCADE"),
        nullable=False,
    )
    position_index: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    spread: Mapped[TarotSpread] = relationship(back_populates="positions", lazy="raise")
