from uuid import UUID

from app.exceptions.base_configuration_exceptions import (
    BaseConfigurationNotFoundException,
)
from app.repositories.base_configuration_repository import (
    BaseConfigurationRepository,
)


class BaseConfigurationService:
    def __init__(
        self,
        repository: BaseConfigurationRepository,
    ):
        self.repository = repository

    def list_configurations(self):
        return self.repository.list_all()

    def get_configuration(self, configuration_id: UUID):
        configuration = self.repository.get_by_id(
            configuration_id
        )

        if configuration is None:
            raise BaseConfigurationNotFoundException()

        return configuration