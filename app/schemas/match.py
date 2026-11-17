from typing import List

from pydantic import BaseModel

from app.schemas.user import UserOut


class MatchOut(BaseModel):
    user: UserOut
    score: float
    mutual: bool
    can_teach_you: List[str]
    wants_to_learn_from_you: List[str]
