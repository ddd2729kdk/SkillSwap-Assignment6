from typing import List, Optional

from fastapi import APIRouter, Query, Response, status

from app.schemas.skill import SkillCategory, SkillCreate, SkillOut, SkillUpdate
from app.schemas.user import UserOut
from app.services import skill_service

router = APIRouter(prefix="/skills", tags=["Skills"])


class TeacherOut(UserOut):
    teaching_level: str


@router.post("", response_model=SkillOut, status_code=status.HTTP_201_CREATED)
def create_skill(data: SkillCreate):
    return skill_service.create_skill(data)


@router.get("", response_model=List[SkillOut])
def list_skills(
    category: Optional[SkillCategory] = Query(default=None),
    search: Optional[str] = Query(default=None, min_length=1),
):
    return skill_service.list_skills(category, search)


@router.get("/{skill_id}", response_model=SkillOut)
def get_skill(skill_id: int):
    return skill_service.get_skill(skill_id)


@router.patch("/{skill_id}", response_model=SkillOut)
def update_skill(skill_id: int, data: SkillUpdate):
    return skill_service.update_skill(skill_id, data)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_skill(skill_id: int):
    skill_service.delete_skill(skill_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{skill_id}/teachers", response_model=List[TeacherOut])
def list_teachers(skill_id: int):
    return skill_service.list_teachers(skill_id)
