from app.exceptions.app_exception import AppException


class InvitationCodeNotFoundException(AppException):
    def __init__(self):
        super().__init__(
            status_code=404,
            detail="Invitation code not found",
        )


class InvitationCodeAlreadyUsedException(AppException):
    def __init__(self):
        super().__init__(
            status_code=409,
            detail="Invitation code has already been used",
        )


class InvitationCodeExpiredException(AppException):
    def __init__(self):
        super().__init__(
            status_code=410,
            detail="Invitation code has expired",
        )