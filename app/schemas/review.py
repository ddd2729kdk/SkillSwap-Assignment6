from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import clean_text


class ReviewCreate(BaseModel):
    swap_id: int = Field(gt=0, examples=[1])
    author_id: int = Field(gt=0, examples=[1])
    rating: int = Field(ge=1, le=5, examples=[5])
    comment: Optional[str] = Field(default=None, max_length=500)

    @field_validator("comment", mode="before")
    @classmethod
    def _clean(cls, value):
        return clean_text(value)


class ReviewUpdate(BaseModel):
    author_id: int = Field(gt=0)
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    comment: Optional[str] = Field(default=None, max_length=500)

    @field_validator("comment", mode="before")
    @classmethod
    def _clean(cls, value):
        return clean_text(value)


class ReviewOut(BaseModel):
    id: int
    swap_id: int
    author_id: int
    reviewee_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime
