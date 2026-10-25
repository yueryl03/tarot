"""Map domain errors onto a single JSON error envelope."""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.errors import TarotError

logger = logging.getLogger(__name__)

STATUS_BY_CODE = {
    "unauthorized": 401,
    "spread_not_found": 404,
    "reading_not_found": 404,
    "interpretation_not_found": 404,
    "validation_error": 422,
    "invalid_draw": 422,
    "invalid_slot": 422,
    "duplicate_slots": 422,
    "invalid_idempotency_key": 422,
    "reading_already_completed": 409,
    "slot_already_revealed": 409,
    "draw_exceeds_spread": 409,
    "draw_exceeds_deck": 409,
    "idempotency_conflict": 409,
    "reading_not_complete": 409,
    "concurrent_conflict": 409,
    "provider_not_configured": 503,
    "interpretation_failed": 502,
    "database_unavailable": 503,
    "deck_integrity": 500,
    "spread_integrity": 500,
}

ERROR_RESPONSES: dict[int, dict[str, str]] = {
    401: {"description": "Missing or invalid reading token."},
    404: {"description": "Resource not found."},
    409: {"description": "The reading state conflicts with the request."},
    422: {"description": "The request body or parameters are invalid."},
    500: {"description": "The server could not complete the request."},
    502: {"description": "The interpretation provider failed."},
    503: {"description": "A required dependency is unavailable."},
}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        return await http_exception_handler(request, exc)  # type: ignore[return-value]

    @app.exception_handler(TarotError)
    async def handle_tarot_error(request: Request, exc: TarotError) -> JSONResponse:
        status = STATUS_BY_CODE.get(exc.code, 400)
        headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
        return JSONResponse(
            status_code=status,
            headers=headers,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors = [
            {
                "loc": [str(item) for item in error.get("loc", ())],
                "msg": str(error.get("msg", "")),
                "type": str(error.get("type", "")),
            }
            for error in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request validation failed.",
                    "details": {"errors": errors},
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", extra={"operation": "unhandled"})
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                    "details": {},
                }
            },
        )
