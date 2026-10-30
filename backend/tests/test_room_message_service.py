from uuid import uuid4

import pytest

from app.models.friend_group import FriendGroup
from app.models.room_message import RoomMessage
from app.models.user import User
from app.repositories.group_membership_repository import (
    GroupMembershipRepository,
)
from app.services.room_message_service import RoomMessageService


def create_test_user(db) -> User:
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed-password",
        display_name="Room Message Test User",
    )
    db.add(user)
    db.flush()
    return user


def create_test_group(db) -> FriendGroup:
    group = FriendGroup(name=f"Room Message Test Group {uuid4()}")
    db.add(group)
    db.flush()
    return group


def add_group_member(db, user_id, group_id):
    repository = GroupMembershipRepository(db)
    repository.create(user_id, group_id)


def create_test_message(db, user_id, group_id) -> RoomMessage:
    message = RoomMessage(
        group_id=group_id,
        user_id=user_id,
        content="Service test message",
    )
    db.add(message)
    db.flush()
    return message


def test_create_message(db):
    user = create_test_user(db)
    group = create_test_group(db)
    add_group_member(db, user.id, group.id)
    service = RoomMessageService(db)

    message = service.create_message(
        group_id=group.id,
        user_id=user.id,
        content="Hello everyone!",
    )

    assert message.id is not None
    assert message.group_id == group.id
    assert message.user_id == user.id
    assert message.content == "Hello everyone!"


def test_create_message_rejects_empty_content(db):
    user = create_test_user(db)
    group = create_test_group(db)
    add_group_member(db, user.id, group.id)
    service = RoomMessageService(db)

    with pytest.raises(ValueError, match="Message content must not be empty"):
        service.create_message(group.id, user.id, "   ")


def test_create_message_rejects_non_member(db):
    user = create_test_user(db)
    group = create_test_group(db)
    service = RoomMessageService(db)

    with pytest.raises(ValueError, match="User is not a member"):
        service.create_message(group.id, user.id, "Hello!")


def test_get_group_messages(db):
    user = create_test_user(db)
    group = create_test_group(db)
    add_group_member(db, user.id, group.id)
    first = create_test_message(db, user.id, group.id)
    service = RoomMessageService(db)

    results = service.get_group_messages(group.id, user.id)

    assert [item.id for item in results] == [first.id]


def test_get_group_messages_rejects_non_member(db):
    user = create_test_user(db)
    group = create_test_group(db)
    service = RoomMessageService(db)

    with pytest.raises(ValueError, match="User is not a member"):
        service.get_group_messages(group.id, user.id)


def test_delete_message(db):
    user = create_test_user(db)
    group = create_test_group(db)
    add_group_member(db, user.id, group.id)
    message = create_test_message(db, user.id, group.id)
    service = RoomMessageService(db)

    assert service.delete_message(message.id, user.id) is True
    assert service.message_repository.get_by_id(message.id) is None


def test_delete_message_rejects_non_creator(db):
    owner = create_test_user(db)
    other_user = create_test_user(db)
    group = create_test_group(db)

    add_group_member(db, owner.id, group.id)
    add_group_member(db, other_user.id, group.id)

    message = create_test_message(db, owner.id, group.id)
    service = RoomMessageService(db)

    with pytest.raises(ValueError, match="Only the message creator"):
        service.delete_message(message.id, other_user.id)


def test_delete_message_rejects_non_member(db):
    owner = create_test_user(db)
    outsider = create_test_user(db)
    group = create_test_group(db)

    add_group_member(db, owner.id, group.id)
    message = create_test_message(db, owner.id, group.id)
    service = RoomMessageService(db)

    with pytest.raises(ValueError, match="User is not a member"):
        service.delete_message(message.id, outsider.id)


def test_delete_message_rejects_missing_message(db):
    user = create_test_user(db)
    service = RoomMessageService(db)

    with pytest.raises(ValueError, match="Room message not found"):
        service.delete_message(uuid4(), user.id)