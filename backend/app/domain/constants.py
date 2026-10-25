"""Physical deck constants.

A reading deck is one finite collection of 78 cards. Upright and reversed are
orientations of those cards, not extra cards, so the deck is never 156 rows.
"""

DECK_SIZE = 78
SLOT_MIN = 0
SLOT_MAX = DECK_SIZE - 1
QUESTION_MIN_LENGTH = 1
QUESTION_MAX_LENGTH = 2000
IDEMPOTENCY_KEY_MAX_LENGTH = 200
ACCESS_TOKEN_BYTES = 32
