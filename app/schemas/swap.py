from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import clean_text, to_utc


class SwapStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"
    cancelled = "cancelled"
    completed = "completed"


class SwapCreate(BaseModel):
    requester_id: int = Field(gt=0, examples=[1])
    partner_id: int = Field(gt=0, examples=[2])
    skill_id: int = Field(gt=0, examples=[1])
    offered_skill_id: Optional[int] = Field(default=None, gt=0, examples=[2])
    message: Optional[str] = Field(default=None, max_length=300)
    scheduled_at: datetime = Field(examples=["2030-01-15T14:00:00Z"])
    duration_minutes: int = Field(default=60, ge=15, le=240)

    @field_validator("message", mode="before")
    @classmethod
    def _clean(cls, value):
        return clean_text(value)

    @field_validator("scheduled_at")
    @classmethod
    def _utc(cls, value):
        return to_utc(value)


class SwapUpdate(BaseModel):
    actor_id: int = Field(gt=0)
    message: Optional[str] = Field(default=None, max_length=300)
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=15, le=240)

    @field_validator("message", mode="before")
    @classmethod
    def _clean(cls, value):
        return clean_text(value)

    @field_validator("scheduled_at")
    @classmethod
    def _utc(cls, value):
        return to_utc(value) if value is not None else value


class SwapStatusUpdate(BaseModel):
    actor_id: int = Field(gt=0)
    status: SwapStatus

    @field_validator("status")
    @classmethod
    def _not_pending(cls, value):
        if value == SwapStatus.pending:
            raise ValueError("status cannot be set back to pending")
        return value


class SwapOut(BaseModel):
    id: int
    requester_id: int
    partner_id: int
    skill_id: int
    skill_name: Optional[str]
    offered_skill_id: Optional[int]
    offered_skill_name: Optional[str]
    message: Optional[str]
    scheduled_at: datetime
    duration_minutes: int
    status: SwapStatus
    created_at: datetime
    updated_at: datetime
