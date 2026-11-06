from app.exceptions.app_exception import AppException


class BaseConfigurationNotFoundException(AppException):
    def __init__(self):
        super().__init__(
            status_code=404,
            detail="Base configuration not found!",
        )