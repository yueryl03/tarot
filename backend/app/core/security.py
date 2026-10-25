"""Reading access tokens.

The raw token is returned once, when the reading is created. PostgreSQL stores
only a SHA-256 hash. The token is high-entropy (256 bits), so a fast hash is
appropriate; this is not a password.
"""

import hashlib
import hmac
import json
from secrets import token_urlsafe
from typing import Any

from app.domain.constants import ACCESS_TOKEN_BYTES, IDEMPOTENCY_KEY_MAX_LENGTH
from app.domain.errors import TarotError

# Compared when a reading id does not exist, so the hash step still runs.
DUMMY_TOKEN_HASH = hashlib.sha256(b"tarot-dummy-access-token").hexdigest()


def generate_access_token() -> str:
    return token_urlsafe(ACCESS_TOKEN_BYTES)


def hash_access_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_access_token(token: str, token_hash: str) -> bool:
    candidate = hash_access_token(token)
    if len(candidate) != len(token_hash):
        return False
    return hmac.compare_digest(candidate, token_hash)


def clean_idempotency_key(value: str | None) -> str | None:
    if value is None:
        return None
    key = value.strip()
    if not key or len(key) > IDEMPOTENCY_KEY_MAX_LENGTH:
        raise TarotError(
            "Idempotency-Key must be between 1 and 200 characters.",
            code="invalid_idempotency_key",
        )
    return key


def canonical_request_hash(payload: dict[str, Any]) -> str:
    """Stable hash of a mutating request body for idempotency checks."""

    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()
