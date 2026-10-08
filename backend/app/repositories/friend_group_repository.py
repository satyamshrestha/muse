from sqlalchemy.orm import Session

from app.models.friend_group import FriendGroup


class FriendGroupRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        name: str,
    ) -> FriendGroup:
        group = FriendGroup(
            name=name,
        )

        self.db.add(group)
        self.db.flush()

        return group