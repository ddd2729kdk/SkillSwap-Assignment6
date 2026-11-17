from typing import List, Optional

from fastapi import APIRouter, Query, Response, status

from app.schemas.match import MatchOut
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services import match_service, user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreate):
    return user_service.create_user(data)


@router.get("", response_model=List[UserOut])
def list_users(
    university: Optional[str] = Query(default=None),
    skill_id: Optional[int] = Query(default=None, gt=0, description="Only users who teach this skill"),
    search: Optional[str] = Query(default=None, min_length=1),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return user_service.list_users(university, skill_id, search, limit, offset)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    return user_service.get_user(user_id)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate):
    return user_service.update_user(user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int):
    user_service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{user_id}/matches", response_model=List[MatchOut])
def get_matches(
    user_id: int,
    min_score: float = Query(default=0, ge=0),
    same_university_only: bool = Query(default=False),
    limit: int = Query(default=10, ge=1, le=50),
):
    return match_service.find_matches(user_id, min_score, same_university_only, limit)
