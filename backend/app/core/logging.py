"""JSON logs with an allow-list of extra fields.

Reading tokens and authorization headers are redacted if they ever reach a
log message. Do not pass ``access_token`` or ``Authorization`` as extra fields;
unknown extras are dropped.
"""

import json
import logging
from datetime import datetime, timezone

_ALLOWED_EXTRAS = ("reading_id", "spread_slug", "operation", "draw_count", "status_code")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        lowered = message.lower()
        if "bearer " in lowered or "access_token" in lowered or "authorization:" in lowered:
            message = "[redacted]"
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
        }
        for key in _ALLOWED_EXTRAS:
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str) -> None:
    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(level.upper())
    # Uvicorn's access log records the request line, not headers. Keep it on
    # the same formatter so application logs stay structured.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        named = logging.getLogger(name)
        named.handlers.clear()
        named.propagate = True
