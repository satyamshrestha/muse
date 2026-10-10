from app.exceptions.app_exception import AppException


class GroupNotFoundException(AppException):
    def __init__(self):
        super().__init__(
            status_code=404,
            detail="Group not found",
        )


class AlreadyGroupMemberException(AppException):
    def __init__(self):
        super().__init__(
            status_code=409,
            detail="You are already a member of this group",
        )