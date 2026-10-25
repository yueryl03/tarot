"""Initial tarot schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tarot_cards",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("arcana_type", sa.String(length=16), nullable=False),
        sa.Column("suit", sa.String(length=16), nullable=True),
        sa.Column("rank", sa.String(length=16), nullable=False),
        sa.Column("canonical_number", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_key", sa.String(length=120), nullable=True),
        sa.CheckConstraint(
            "arcana_type IN ('major', 'minor')",
            name="ck_tarot_cards_arcana_type",
        ),
        sa.CheckConstraint(
            "suit IS NULL OR suit IN ('wands', 'cups', 'swords', 'pentacles')",
            name="ck_tarot_cards_suit",
        ),
        sa.CheckConstraint(
            "(arcana_type = 'major' AND suit IS NULL) "
            "OR (arcana_type = 'minor' AND suit IS NOT NULL)",
            name="ck_tarot_cards_suit_matches_arcana",
        ),
        sa.CheckConstraint(
            "canonical_number >= 0 AND canonical_number <= 77",
            name="ck_tarot_cards_canonical_number",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("canonical_number"),
        sa.UniqueConstraint("image_key"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "tarot_meanings",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("orientation", sa.String(length=16), nullable=False),
        sa.Column("general_meaning", sa.Text(), nullable=False),
        sa.Column("keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("love_meaning", sa.Text(), nullable=True),
        sa.Column("career_meaning", sa.Text(), nullable=True),
        sa.Column("advice", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "orientation IN ('upright', 'reversed')",
            name="ck_tarot_meanings_orientation",
        ),
        sa.ForeignKeyConstraint(["card_id"], ["tarot_cards.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "card_id",
            "orientation",
            name="uq_tarot_meanings_card_orientation",
        ),
    )
    op.create_table(
        "tarot_spreads",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("card_count", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("card_count > 0", name="ck_tarot_spreads_card_count"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "tarot_spread_positions",
        sa.Column("id", sa.Integer(), sa.Identity(always=False), nullable=False),
        sa.Column("spread_id", sa.Integer(), nullable=False),
        sa.Column("position_index", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "position_index >= 0",
            name="ck_tarot_spread_positions_index",
        ),
        sa.ForeignKeyConstraint(["spread_id"], ["tarot_spreads.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "spread_id",
            "position_index",
            name="uq_tarot_spread_positions_spread_index",
        ),
    )
    op.create_table(
        "reading_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("spread_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default="created",
            nullable=False,
        ),
        sa.Column("reversals_enabled", sa.Boolean(), nullable=False),
        sa.Column("access_token_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('created', 'in_progress', 'completed')",
            name="ck_reading_sessions_status",
        ),
        sa.CheckConstraint(
            "char_length(question) BETWEEN 1 AND 2000",
            name="ck_reading_sessions_question_length",
        ),
        sa.CheckConstraint(
            "char_length(access_token_hash) = 64",
            name="ck_reading_sessions_token_hash_length",
        ),
        sa.ForeignKeyConstraint(["spread_id"], ["tarot_spreads.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_reading_sessions_spread_id",
        "reading_sessions",
        ["spread_id"],
    )
    op.create_table(
        "reading_deck_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reading_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("card_id", sa.Integer(), nullable=False),
        sa.Column("slot_index", sa.Integer(), nullable=False),
        sa.Column("orientation", sa.String(length=16), nullable=False),
        sa.CheckConstraint(
            "slot_index >= 0 AND slot_index <= 77",
            name="ck_reading_deck_slots_slot_index",
        ),
        sa.CheckConstraint(
            "orientation IN ('upright', 'reversed')",
            name="ck_reading_deck_slots_orientation",
        ),
        sa.ForeignKeyConstraint(["card_id"], ["tarot_cards.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["reading_id"],
            ["reading_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "reading_id",
            "card_id",
            name="uq_reading_deck_slots_reading_card",
        ),
        sa.UniqueConstraint(
            "reading_id",
            "id",
            name="uq_reading_deck_slots_reading_id_id",
        ),
        sa.UniqueConstraint(
            "reading_id",
            "slot_index",
            name="uq_reading_deck_slots_reading_slot",
        ),
    )
    op.create_index(
        "ix_reading_deck_slots_card_id",
        "reading_deck_slots",
        ["card_id"],
    )
    op.create_table(
        "reading_draws",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reading_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deck_slot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("spread_position_index", sa.Integer(), nullable=False),
        sa.Column(
            "revealed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "spread_position_index >= 0",
            name="ck_reading_draws_position_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["reading_id", "deck_slot_id"],
            ["reading_deck_slots.reading_id", "reading_deck_slots.id"],
            name="fk_reading_draws_slot_same_reading",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reading_id"],
            ["reading_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("deck_slot_id", name="uq_reading_draws_deck_slot"),
        sa.UniqueConstraint(
            "reading_id",
            "spread_position_index",
            name="uq_reading_draws_reading_position",
        ),
    )
    op.create_table(
        "interpretations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reading_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("model_name", sa.String(length=120), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("interpretation_text", sa.Text(), nullable=False),
        sa.Column(
            "structured_result",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["reading_id"],
            ["reading_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_interpretations_reading_id",
        "interpretations",
        ["reading_id"],
    )
    op.create_table(
        "idempotency_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reading_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("operation", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column("request_hash", sa.String(length=64), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("response_body", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["reading_id"],
            ["reading_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "reading_id",
            "operation",
            "idempotency_key",
            name="uq_idempotency_keys_reading_operation_key",
        ),
    )
    op.execute(_DECK_SIZE_FUNCTION)
    op.execute(_ORIENTATION_FUNCTION)
    op.execute(_IMMUTABLE_SLOT_FUNCTION)
    op.execute(_DRAW_POSITION_FUNCTION)
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER trg_reading_sessions_deck_size
        AFTER INSERT ON reading_sessions
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE FUNCTION enforce_reading_deck_size()
        """
    )
    op.execute(
        """
        CREATE CONSTRAINT TRIGGER trg_reading_deck_slots_deck_size
        AFTER INSERT OR DELETE ON reading_deck_slots
        DEFERRABLE INITIALLY DEFERRED
        FOR EACH ROW
        EXECUTE FUNCTION enforce_reading_deck_size()
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_deck_slot_orientation
        BEFORE INSERT ON reading_deck_slots
        FOR EACH ROW
        EXECUTE FUNCTION enforce_slot_orientation_policy()
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_deck_slot_immutable
        BEFORE UPDATE ON reading_deck_slots
        FOR EACH ROW
        EXECUTE FUNCTION prevent_deck_slot_mutation()
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_draw_position_range
        BEFORE INSERT ON reading_draws
        FOR EACH ROW
        EXECUTE FUNCTION enforce_draw_position_range()
        """
    )
    op.execute(
        """
        COMMENT ON TABLE reading_deck_slots IS
        'One physical shuffled deck. Exactly 78 rows after the reading transaction commits. Orientation is fixed at creation and is not re-sampled when a card is revealed.'
        """
    )
    op.execute(
        """
        COMMENT ON TABLE reading_sessions IS
        'One reading is one shuffled physical deck. access_token_hash is a SHA-256 hex digest. The raw token is never stored.'
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_draw_position_range ON reading_draws")
    op.execute("DROP TRIGGER IF EXISTS trg_deck_slot_immutable ON reading_deck_slots")
    op.execute("DROP TRIGGER IF EXISTS trg_deck_slot_orientation ON reading_deck_slots")
    op.execute(
        "DROP TRIGGER IF EXISTS trg_reading_deck_slots_deck_size ON reading_deck_slots"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_reading_sessions_deck_size ON reading_sessions"
    )
    op.execute("DROP FUNCTION IF EXISTS enforce_draw_position_range()")
    op.execute("DROP FUNCTION IF EXISTS prevent_deck_slot_mutation()")
    op.execute("DROP FUNCTION IF EXISTS enforce_slot_orientation_policy()")
    op.execute("DROP FUNCTION IF EXISTS enforce_reading_deck_size()")
    op.drop_table("idempotency_keys")
    op.drop_index("ix_interpretations_reading_id", table_name="interpretations")
    op.drop_table("interpretations")
    op.drop_table("reading_draws")
    op.drop_index("ix_reading_deck_slots_card_id", table_name="reading_deck_slots")
    op.drop_table("reading_deck_slots")
    op.drop_index("ix_reading_sessions_spread_id", table_name="reading_sessions")
    op.drop_table("reading_sessions")
    op.drop_table("tarot_spread_positions")
    op.drop_table("tarot_spreads")
    op.drop_table("tarot_meanings")
    op.drop_table("tarot_cards")


_DECK_SIZE_FUNCTION = """
CREATE FUNCTION enforce_reading_deck_size()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    reading_uuid uuid;
    slot_count integer;
BEGIN
    IF TG_TABLE_NAME = 'reading_sessions' THEN
        reading_uuid := NEW.id;
    ELSE
        reading_uuid := COALESCE(NEW.reading_id, OLD.reading_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM reading_sessions WHERE id = reading_uuid) THEN
        RETURN NULL;
    END IF;

    SELECT COUNT(*) INTO slot_count
    FROM reading_deck_slots
    WHERE reading_id = reading_uuid;

    IF slot_count <> 78 THEN
        RAISE EXCEPTION 'reading % must have exactly 78 deck slots, found %',
            reading_uuid, slot_count;
    END IF;
    RETURN NULL;
END;
$$
"""

_ORIENTATION_FUNCTION = """
CREATE FUNCTION enforce_slot_orientation_policy()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    reversals boolean;
BEGIN
    SELECT reversals_enabled INTO reversals
    FROM reading_sessions
    WHERE id = NEW.reading_id;

    IF reversals IS NULL THEN
        RAISE EXCEPTION 'reading % does not exist for deck slot', NEW.reading_id;
    END IF;

    IF NOT reversals AND NEW.orientation <> 'upright' THEN
        RAISE EXCEPTION 'reading % has reversals disabled; orientation must be upright',
            NEW.reading_id;
    END IF;
    RETURN NEW;
END;
$$
"""

_IMMUTABLE_SLOT_FUNCTION = """
CREATE FUNCTION prevent_deck_slot_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.card_id IS DISTINCT FROM OLD.card_id
       OR NEW.orientation IS DISTINCT FROM OLD.orientation
       OR NEW.slot_index IS DISTINCT FROM OLD.slot_index
       OR NEW.reading_id IS DISTINCT FROM OLD.reading_id THEN
        RAISE EXCEPTION 'reading deck slots are immutable';
    END IF;
    RETURN NEW;
END;
$$
"""

_DRAW_POSITION_FUNCTION = """
CREATE FUNCTION enforce_draw_position_range()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    max_cards integer;
BEGIN
    SELECT s.card_count INTO max_cards
    FROM reading_sessions r
    JOIN tarot_spreads s ON s.id = r.spread_id
    WHERE r.id = NEW.reading_id;

    IF max_cards IS NULL THEN
        RAISE EXCEPTION 'reading % is missing a spread', NEW.reading_id;
    END IF;

    IF NEW.spread_position_index < 0 OR NEW.spread_position_index >= max_cards THEN
        RAISE EXCEPTION 'spread position % is outside 0..% for reading %',
            NEW.spread_position_index, max_cards - 1, NEW.reading_id;
    END IF;
    RETURN NEW;
END;
$$
"""
