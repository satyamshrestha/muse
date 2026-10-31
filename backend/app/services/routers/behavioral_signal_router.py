from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.jwt import get_current_user_id
from app.schemas.behavioral_signal_schema import (
    BehavioralSignalCreate,
    BehavioralSignalRead,
)
from app.services.dependencies import get_behavioral_signal_service
from app.services.behavioral_signal_service import (
    BehavioralSignalService,
)


router = APIRouter(
    prefix="/behavioral-signals",
    tags=["behavioral-signals"],
)


def _raise_signal_error(error: ValueError) -> None:
    message = str(error)

    if "not found" in message.lower():
        code = status.HTTP_404_NOT_FOUND
    elif "must not be empty" in message.lower():
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
    else:
        code = status.HTTP_403_FORBIDDEN

    raise HTTPException(
        status_code=code,
        detail=message,
    ) from error


@router.post(
    "",
    response_model=BehavioralSignalRead,
    status_code=status.HTTP_201_CREATED,
)
def create_signal(
    payload: BehavioralSignalCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: BehavioralSignalService = Depends(
        get_behavioral_signal_service
    ),
):
    try:
        return service.create_signal(
            user_id=user_id,
            signal_type=payload.signal_type,
            value=payload.value,
        )
    except ValueError as error:
        _raise_signal_error(error)


@router.get(
    "",
    response_model=list[BehavioralSignalRead],
)
def list_signals(
    user_id: UUID = Depends(get_current_user_id),
    service: BehavioralSignalService = Depends(
        get_behavioral_signal_service
    ),
):
    return service.get_user_signals(user_id)


@router.get(
    "/type/{signal_type}",
    response_model=list[BehavioralSignalRead],
)
def list_signals_by_type(
    signal_type: str,
    user_id: UUID = Depends(get_current_user_id),
    service: BehavioralSignalService = Depends(
        get_behavioral_signal_service
    ),
):
    try:
        return service.get_user_signals_by_type(
            user_id=user_id,
            signal_type=signal_type,
        )
    except ValueError as error:
        _raise_signal_error(error)


@router.delete(
    "/{signal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_signal(
    signal_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: BehavioralSignalService = Depends(
        get_behavioral_signal_service
    ),
):
    try:
        service.delete_signal(
            signal_id=signal_id,
            user_id=user_id,
        )
    except ValueError as error:
        _raise_signal_error(error)

    return Response(status_code=status.HTTP_204_NO_CONTENT)