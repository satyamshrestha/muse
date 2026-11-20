from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.friend_group import FriendGroup
from app.models.group_membership import GroupMembership
from app.models.user import User
from app.repositories.friend_group_repository import FriendGroupRepository


def create_user(db: Session) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_group(db: Session, name: str = "Test Group") -> FriendGroup:
    group = FriendGroup(name=name)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def test_create_group(db: Session):
    repository = FriendGroupRepository(db)

    group = repository.create("Test Group")
    db.commit()
    db.refresh(group)

    assert group.id is not None
    assert group.name == "Test Group"
    assert group.created_at is not None

    persisted = db.get(FriendGroup, group.id)
    assert persisted is not None


def test_get_by_id_returns_existing_group(db: Session):
    group = create_group(db)
    repository = FriendGroupRepository(db)

    result = repository.get_by_id(group.id)

    assert result is not None
    assert result.id == group.id
    assert result.name == group.name


def test_get_by_id_returns_none_for_missing_group(db: Session):
    repository = FriendGroupRepository(db)

    result = repository.get_by_id(uuid4())

    assert result is None


def test_delete_removes_existing_group(db: Session):
    group = create_group(db)
    repository = FriendGroupRepository(db)

    repository.delete(group.id)
    db.commit()

    assert db.get(FriendGroup, group.id) is None


def test_delete_missing_group_does_not_raise(db: Session):
    repository = FriendGroupRepository(db)

    repository.delete(uuid4())
    db.commit()


def test_delete_group_cascades_to_memberships(db: Session):
    user = create_user(db)
    group = create_group(db)

    membership = GroupMembership(
        user_id=user.id,
        group_id=group.id,
    )
    db.add(membership)
    db.commit()

    repository = FriendGroupRepository(db)

    repository.delete(group.id)
    db.commit()

    remaining_memberships = db.scalar(
        select(func.count())
        .select_from(GroupMembership)
        .where(GroupMembership.group_id == group.id)
    )

    assert db.get(FriendGroup, group.id) is None
    assert remaining_memberships == 0