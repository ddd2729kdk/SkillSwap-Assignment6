from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import clean_text


class SkillCategory(str, Enum):
    programming = "programming"
    languages = "languages"
    design = "design"
    music = "music"
    science = "science"
    business = "business"
    sports = "sports"
    other = "other"


class SkillCreate(BaseModel):
    name: str = Field(min_length=2, max_length=50, examples=["Python"])
    category: SkillCategory = Field(examples=["programming"])
    description: Optional[str] = Field(default=None, max_length=300)

    @field_validator("name", "description", mode="before")
    @classmethod
    def _clean(cls, value):
        return clean_text(value)


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=50)
    category: Optional[SkillCategory] = None
    description: Optional[str] = Field(default=None, max_length=300)

    @field_validator("name", "description", mode="before")
    @classmethod
    def _clean(cls, value):
        return clean_text(value)


class SkillOut(BaseModel):
    id: int
    name: str
    category: SkillCategory
    description: Optional[str]
