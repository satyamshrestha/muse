from app.exceptions.app_exception import AppException

class UserAlreadyExistsException(AppException):
    def __init__(self):
        super().__init__(
            status_code=409,
            detail="User already exists!"
        )

class UserNotFoundException(AppException):
    def __init__(self):
        super().__init__(
            status_code=409,
            detail="User not found!"
        )

class InvalidCredentialsException(AppException):
    def __init__(self):
        super().__init__(
            status_code=401,
            detail="Invalid Credentials! Please try again!"
        )