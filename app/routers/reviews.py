from typing import List, Optional

from fastapi import APIRouter, Query, Response, status

from app.schemas.review import ReviewCreate, ReviewOut, ReviewUpdate
from app.services import review_service

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(data: ReviewCreate):
    return review_service.create_review(data)


@router.get("", response_model=List[ReviewOut])
def list_reviews(
    user_id: Optional[int] = Query(default=None, gt=0, description="Reviews received by this user"),
    swap_id: Optional[int] = Query(default=None, gt=0),
    min_rating: Optional[int] = Query(default=None, ge=1, le=5),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return review_service.list_reviews(user_id, swap_id, min_rating, limit, offset)


@router.get("/{review_id}", response_model=ReviewOut)
def get_review(review_id: int):
    return review_service.get_review(review_id)


@router.patch("/{review_id}", response_model=ReviewOut)
def update_review(review_id: int, data: ReviewUpdate):
    return review_service.update_review(review_id, data)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: int, author_id: int = Query(gt=0)):
    review_service.delete_review(review_id, author_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
