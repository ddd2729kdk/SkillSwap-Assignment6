from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import clean_text


class SkillKind(str, Enum):
    offer = "offer"
    want = "want"


class SkillLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class UserSkillCreate(BaseModel):
    skill_id: int = Field(gt=0, examples=[1])
    kind: SkillKind = Field(examples=["offer"])
    level: SkillLevel = Field(examples=["intermediate"])
    note: Optional[str] = Field(default=None, max_length=200)

    @field_validator("note", mode="before")
    @classmethod
    def _clean(cls, value):
        return clean_text(value)


class UserSkillUpdate(BaseModel):
    level: Optional[SkillLevel] = None
    note: Optional[str] = Field(default=None, max_length=200)

    @field_validator("note", mode="before")
    @classmethod
    def _clean(cls, value):
        return clean_text(value)


class UserSkillOut(BaseModel):
    id: int
    user_id: int
    skill_id: int
    skill_name: str
    kind: SkillKind
    level: SkillLevel
    note: Optional[str]
