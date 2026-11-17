from typing import List, Optional

from fastapi import APIRouter, Query, Response, status

from app.schemas.user_skill import SkillKind, UserSkillCreate, UserSkillOut, UserSkillUpdate
from app.services import user_skill_service

router = APIRouter(prefix="/users/{user_id}/skills", tags=["User Skills"])


@router.post("", response_model=UserSkillOut, status_code=status.HTTP_201_CREATED)
def add_user_skill(user_id: int, data: UserSkillCreate):
    return user_skill_service.add_user_skill(user_id, data)


@router.get("", response_model=List[UserSkillOut])
def list_user_skills(user_id: int, kind: Optional[SkillKind] = Query(default=None)):
    return user_skill_service.list_user_skills(user_id, kind)


@router.patch("/{record_id}", response_model=UserSkillOut)
def update_user_skill(user_id: int, record_id: int, data: UserSkillUpdate):
    return user_skill_service.update_user_skill(user_id, record_id, data)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user_skill(user_id: int, record_id: int):
    user_skill_service.remove_user_skill(user_id, record_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
