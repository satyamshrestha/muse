
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.friend_group import FriendGroup


class FriendGroupRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str) -> FriendGroup:
        group = FriendGroup(name=name)
        self.db.add(group)
        self.db.flush()
        return group

    def get_by_id(self, group_id: UUID) -> FriendGroup | None:
        return self.db.scalar(
            select(FriendGroup).where(
                FriendGroup.id == group_id
            )
        )