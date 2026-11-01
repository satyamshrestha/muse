from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.jwt import get_current_user_id
from app.schemas.daily_drop_schema import DailyDropCreate, DailyDropRead
from app.services.daily_drop_service import DailyDropService
from app.services.dependencies import get_daily_drop_service


router = APIRouter(
    prefix="/daily-drops",
    tags=["Daily Drops"],
)


@router.post(
    "",
    response_model=DailyDropRead,
    status_code=status.HTTP_201_CREATED,
)
def create_daily_drop(
    payload: DailyDropCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: DailyDropService = Depends(get_daily_drop_service),
):
    try:
        return service.create_drop(
            user_id=user_id,
            title=payload.title,
            content=payload.content,
            drop_date=payload.drop_date,
            source=payload.source,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[DailyDropRead],
)
def get_daily_drops(
    user_id: UUID = Depends(get_current_user_id),
    service: DailyDropService = Depends(get_daily_drop_service),
):
    return service.get_user_drops(user_id)


@router.get(
    "/date/{drop_date}",
    response_model=list[DailyDropRead],
)
def get_daily_drops_by_date(
    drop_date: date,
    user_id: UUID = Depends(get_current_user_id),
    service: DailyDropService = Depends(get_daily_drop_service),
):
    return service.get_drops_by_date(user_id, drop_date)


@router.get(
    "/{drop_id}",
    response_model=DailyDropRead,
)
def get_daily_drop(
    drop_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: DailyDropService = Depends(get_daily_drop_service),
):
    drop = service.get_drop(user_id, drop_id)

    if drop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily drop not found",
        )

    return drop


@router.delete(
    "/{drop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_daily_drop(
    drop_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: DailyDropService = Depends(get_daily_drop_service),
):
    try:
        service.delete_drop(user_id, drop_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily drop not found",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)