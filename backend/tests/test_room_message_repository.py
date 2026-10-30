from uuid import uuid4

from app.models.friend_group import FriendGroup
from app.models.room_message import RoomMessage
from app.models.user import User
from app.repositories.room_message_repository import RoomMessageRepository


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


def create_test_message(db, user_id, group_id, content="Repository test message"):
    message = RoomMessage(
        group_id=group_id,
        user_id=user_id,
        content=content,
    )
    db.add(message)
    db.flush()
    return message


def test_create_room_message(db):
    user = create_test_user(db)
    group = create_test_group(db)
    repository = RoomMessageRepository(db)

    message = repository.create(
        group_id=group.id,
        user_id=user.id,
        content="Hello everyone!",
    )

    assert message.id is not None
    assert message.group_id == group.id
    assert message.user_id == user.id
    assert message.content == "Hello everyone!"
    assert message.created_at is not None


def test_get_by_id_returns_message(db):
    user = create_test_user(db)
    group = create_test_group(db)
    message = create_test_message(db, user.id, group.id)
    repository = RoomMessageRepository(db)

    result = repository.get_by_id(message.id)

    assert result is not None
    assert result.id == message.id


def test_get_by_id_returns_none_when_missing(db):
    repository = RoomMessageRepository(db)

    assert repository.get_by_id(uuid4()) is None


def test_get_for_group_returns_only_matching_messages(db):
    first_user = create_test_user(db)
    second_user = create_test_user(db)
    first_group = create_test_group(db)
    second_group = create_test_group(db)

    first_message = create_test_message(db, first_user.id, first_group.id)
    create_test_message(db, second_user.id, second_group.id)

    repository = RoomMessageRepository(db)

    results = repository.get_for_group(first_group.id)

    assert [item.id for item in results] == [first_message.id]


def test_get_for_user_returns_only_matching_messages(db):
    first_user = create_test_user(db)
    second_user = create_test_user(db)
    group = create_test_group(db)

    first_message = create_test_message(db, first_user.id, group.id)
    create_test_message(db, second_user.id, group.id)

    repository = RoomMessageRepository(db)

    results = repository.get_for_user(first_user.id)

    assert [item.id for item in results] == [first_message.id]


def test_delete_room_message(db):
    user = create_test_user(db)
    group = create_test_group(db)
    message = create_test_message(db, user.id, group.id)
    repository = RoomMessageRepository(db)

    assert repository.delete(message.id) is True
    assert repository.get_by_id(message.id) is None


def test_delete_returns_false_when_message_missing(db):
    repository = RoomMessageRepository(db)

    assert repository.delete(uuid4()) is False