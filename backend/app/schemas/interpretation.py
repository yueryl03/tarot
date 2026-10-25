"""Interpretation responses."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.interpretation import StructuredInterpretation


class InterpretationResponse(BaseModel):
    id: UUID
    reading_id: UUID
    provider: str
    model_name: str
    interpretation_text: str
    structured_result: StructuredInterpretation
    created_at: datetime
