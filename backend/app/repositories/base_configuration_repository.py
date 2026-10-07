from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base_configuration import BaseConfiguration


class BaseConfigurationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_name(
        self,
        name: str,
    ) -> BaseConfiguration | None:
        return self.db.scalar(
            select(BaseConfiguration).where(
                BaseConfiguration.name == name
            )
        )

    def get_by_id(
        self,
        configuration_id: UUID,
    ) -> BaseConfiguration | None:
        return self.db.scalar(
            select(BaseConfiguration).where(
                BaseConfiguration.id == configuration_id
            )
        )