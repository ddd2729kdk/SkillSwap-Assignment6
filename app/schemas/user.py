from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import clean_text

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=80, examples=["Aigerim Sadykova"])
    email: str = Field(pattern=EMAIL_PATTERN, max_length=120, examples=["aigerim@university.kz"])
    university: str = Field(min_length=2, max_length=120, examples=["Satbayev University"])
    major: str = Field(min_length=2, max_length=100, examples=["Software Engineering"])
    year_of_study: int = Field(ge=1, le=6, examples=[2])
    bio: Optional[str] = Field(default=None, max_length=500)

    @field_validator("full_name", "university", "major", "bio", mode="before")
    @classmethod
    def _clean(cls, value):
        return clean_text(value)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    email: Optional[str] = Field(default=None, pattern=EMAIL_PATTERN, max_length=120)
    university: Optional[str] = Field(default=None, min_length=2, max_length=120)
    major: Optional[str] = Field(default=None, min_length=2, max_length=100)
    year_of_study: Optional[int] = Field(default=None, ge=1, le=6)
    bio: Optional[str] = Field(default=None, max_length=500)

    @field_validator("full_name", "university", "major", "bio", mode="before")
    @classmethod
    def _clean(cls, value):
        return clean_text(value)


class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    university: str
    major: str
    year_of_study: int
    bio: Optional[str]
    average_rating: Optional[float]
    reviews_count: int
    created_at: datetime
