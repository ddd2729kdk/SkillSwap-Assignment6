from typing import List, Literal, Optional

from fastapi import APIRouter, Query, Response, status

from app.schemas.swap import SwapCreate, SwapOut, SwapStatus, SwapStatusUpdate, SwapUpdate
from app.services import swap_service

router = APIRouter(prefix="/swaps", tags=["Swaps"])


@router.post("", response_model=SwapOut, status_code=status.HTTP_201_CREATED)
def create_swap(data: SwapCreate):
    return swap_service.create_swap(data)


@router.get("", response_model=List[SwapOut])
def list_swaps(
    user_id: Optional[int] = Query(default=None, gt=0),
    status: Optional[SwapStatus] = Query(default=None),
    role: Optional[Literal["requester", "partner"]] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return swap_service.list_swaps(user_id, status, role, limit, offset)


@router.get("/{swap_id}", response_model=SwapOut)
def get_swap(swap_id: int):
    return swap_service.get_swap(swap_id)


@router.patch("/{swap_id}", response_model=SwapOut)
def update_swap(swap_id: int, data: SwapUpdate):
    return swap_service.update_swap(swap_id, data)


@router.patch("/{swap_id}/status", response_model=SwapOut)
def change_swap_status(swap_id: int, data: SwapStatusUpdate):
    return swap_service.change_status(swap_id, data)


@router.delete("/{swap_id}", status_code=204)
def delete_swap(swap_id: int, actor_id: int = Query(gt=0)):
    swap_service.delete_swap(swap_id, actor_id)
    return Response(status_code=204)
