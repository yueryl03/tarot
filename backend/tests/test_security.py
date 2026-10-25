"""Token hashing and log redaction."""

import json
import logging

from app.core.logging import JsonFormatter, configure_logging
from app.core.security import (
    canonical_request_hash,
    generate_access_token,
    hash_access_token,
    verify_access_token,
)


def test_access_token_is_hashed_and_not_recoverable_from_the_digest() -> None:
    token = generate_access_token()
    other = generate_access_token()
    digest = hash_access_token(token)
    assert token != other
    assert len(token) >= 40
    assert len(digest) == 64
    assert token not in digest
    assert verify_access_token(token, digest)
    assert not verify_access_token(other, digest)
    assert not verify_access_token(token + "x", digest)


def test_request_hash_ignores_key_order() -> None:
    left = canonical_request_hash({"mode": "select", "slot_indices": [12, 40, 7]})
    right = canonical_request_hash({"slot_indices": [12, 40, 7], "mode": "select"})
    assert left == right
    assert left != canonical_request_hash({"mode": "select", "slot_indices": [7, 40, 12]})


def test_log_formatter_drops_bearer_tokens_and_unknown_extras() -> None:
    configure_logging("INFO")
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="app.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Authorization: Bearer super-secret-token",
        args=(),
        exc_info=None,
    )
    record.reading_id = "reading-1"
    record.access_token = "super-secret-token"
    rendered = formatter.format(record)
    payload = json.loads(rendered)
    assert "super-secret-token" not in rendered
    assert payload["message"] == "[redacted]"
    assert payload["reading_id"] == "reading-1"
    assert "access_token" not in payload
