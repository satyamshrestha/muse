
from uuid import UUID

from fastapi import APIRouter, Depends

from app.auth.jwt import get_current_user_id
from app.schemas.group_schema import GroupCreate, GroupResponse
from app.services.dependencies import get_group_service
from app.services.group_service import GroupService


router = APIRouter(
    prefix="/groups",
    tags=["groups"],
)


@router.post(
    "",
    response_model=GroupResponse,
    status_code=201,
)
def create_group(
    data: GroupCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupService = Depends(get_group_service),
):
    return service.create_group(
        user_id=user_id,
        name=data.name,
    )


@router.get(
    "",
    response_model=list[GroupResponse],
)
def list_groups(
    user_id: UUID = Depends(get_current_user_id),
    service: GroupService = Depends(get_group_service),
):
    return service.get_user_groups(user_id)


@router.get(
    "/{group_id}",
    response_model=GroupResponse,
)
def get_group(
    group_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupService = Depends(get_group_service),
):
    return service.get_group(
        user_id=user_id,
        group_id=group_id,
    )