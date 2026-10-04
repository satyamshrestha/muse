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