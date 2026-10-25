"""Version 1 routes."""

from fastapi import APIRouter

from app.api.v1 import cards, interpretations, readings, spreads

router = APIRouter()
router.include_router(cards.router)
router.include_router(spreads.router)
router.include_router(readings.router)
router.include_router(interpretations.router)
