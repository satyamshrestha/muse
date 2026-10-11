from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.auth.jwt import get_current_user_id
from app.schemas.group_schema import (
    GroupCreate,
    GroupResponse,
    GroupMemberResponse,
    GroupInvitationCreateResponse,
    GroupInvitationRedeem,
)
from app.services.dependencies import get_group_service
from app.services.group_service import GroupService


router = APIRouter(prefix="/groups", tags=["groups"])


@router.post(
    "",
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_group(
    data: GroupCreate,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupService = Depends(get_group_service),
):
    return service.create_group(user_id=user_id, name=data.name)


@router.get("", response_model=list[GroupResponse])
def list_groups(
    user_id: UUID = Depends(get_current_user_id),
    service: GroupService = Depends(get_group_service),
):
    return service.get_user_groups(user_id)


@router.post(
    "/join",
    response_model=GroupResponse,
)
def join_group_with_invitation(
    data: GroupInvitationRedeem,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupService = Depends(get_group_service),
):
    return service.join_group_with_invitation(
        user_id=user_id,
        token=data.token,
    )


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupService = Depends(get_group_service),
):
    return service.get_group(user_id=user_id, group_id=group_id)


@router.get(
    "/{group_id}/members",
    response_model=list[GroupMemberResponse],
)
def get_group_members(
    group_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupService = Depends(get_group_service),
):
    return service.get_group_members(user_id=user_id, group_id=group_id)


@router.post(
    "/{group_id}/invitations",
    response_model=GroupInvitationCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_group_invitation(
    group_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupService = Depends(get_group_service),
):
    return service.create_invitation(user_id=user_id, group_id=group_id)


@router.delete("/{group_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_group(
    group_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: GroupService = Depends(get_group_service),
):
    service.leave_group(user_id=user_id, group_id=group_id)