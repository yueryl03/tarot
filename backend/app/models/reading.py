"""One anonymous reading session and the token hash that guards it."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReadingSession(Base):
    __tablename__ = "reading_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('created', 'in_progress', 'completed')",
            name="ck_reading_sessions_status",
        ),
        CheckConstraint(
            "char_length(question) BETWEEN 1 AND 2000",
            name="ck_reading_sessions_question_length",
        ),
        CheckConstraint(
            "char_length(access_token_hash) = 64",
            name="ck_reading_sessions_token_hash_length",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    spread_id: Mapped[int] = mapped_column(
        ForeignKey("tarot_spreads.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="created",
    )
    reversals_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    access_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
