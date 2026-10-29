from uuid import uuid4

from app.models.friend_group import FriendGroup
from app.models.message_reaction import MessageReaction
from app.models.room_message import RoomMessage
from app.models.user import User
from app.repositories.message_reaction_repository import (
    MessageReactionRepository,
)


def create_test_user(db) -> User:
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed-password",
        display_name="Reaction Test User",
    )
    db.add(user)
    db.flush()
    return user


def create_test_group(db) -> FriendGroup:
    group = FriendGroup(name=f"Reaction Test Group {uuid4()}")
    db.add(group)
    db.flush()
    return group


def create_test_message(db, user_id, group_id) -> RoomMessage:
    message = RoomMessage(
        group_id=group_id,
        user_id=user_id,
        content="Repository test message",
    )
    db.add(message)
    db.flush()
    return message


def test_create_message_reaction(db):
    user = create_test_user(db)
    group = create_test_group(db)
    message = create_test_message(db, user.id, group.id)
    repository = MessageReactionRepository(db)

    reaction = repository.create(
        message_id=message.id,
        user_id=user.id,
        reaction="👍",
    )

    assert reaction.id is not None
    assert reaction.message_id == message.id
    assert reaction.user_id == user.id
    assert reaction.reaction == "👍"


def test_get_by_id_returns_reaction(db):
    user = create_test_user(db)
    group = create_test_group(db)
    message = create_test_message(db, user.id, group.id)
    repository = MessageReactionRepository(db)
    created = repository.create(message.id, user.id, "❤️")

    result = repository.get_by_id(created.id)

    assert result is not None
    assert result.id == created.id


def test_get_by_id_returns_none_when_missing(db):
    repository = MessageReactionRepository(db)

    assert repository.get_by_id(uuid4()) is None


def test_get_for_message_returns_only_matching_reactions(db):
    user = create_test_user(db)
    group = create_test_group(db)
    first_message = create_test_message(db, user.id, group.id)
    second_message = create_test_message(db, user.id, group.id)
    repository = MessageReactionRepository(db)

    first = repository.create(first_message.id, user.id, "👍")
    repository.create(second_message.id, user.id, "😂")

    results = repository.get_for_message(first_message.id)

    assert [item.id for item in results] == [first.id]


def test_get_for_user_and_message_returns_matching_reaction(db):
    user = create_test_user(db)
    group = create_test_group(db)
    message = create_test_message(db, user.id, group.id)
    repository = MessageReactionRepository(db)
    created = repository.create(message.id, user.id, "🔥")

    result = repository.get_for_user_and_message(
        user_id=user.id,
        message_id=message.id,
    )

    assert result is not None
    assert result.id == created.id


def test_get_for_user_and_message_returns_none_when_missing(db):
    user = create_test_user(db)
    group = create_test_group(db)
    message = create_test_message(db, user.id, group.id)
    repository = MessageReactionRepository(db)

    assert repository.get_for_user_and_message(
        user_id=user.id,
        message_id=message.id,
    ) is None


def test_update_reaction(db):
    user = create_test_user(db)
    group = create_test_group(db)
    message = create_test_message(db, user.id, group.id)
    repository = MessageReactionRepository(db)
    created = repository.create(message.id, user.id, "👍")

    updated = repository.update_reaction(
        created,
        reaction="🎉",
    )

    assert updated.reaction == "🎉"


def test_delete_reaction(db):
    user = create_test_user(db)
    group = create_test_group(db)
    message = create_test_message(db, user.id, group.id)
    repository = MessageReactionRepository(db)
    created = repository.create(message.id, user.id, "👍")

    assert repository.delete(created.id) is True
    assert repository.get_by_id(created.id) is None


def test_delete_returns_false_when_reaction_missing(db):
    repository = MessageReactionRepository(db)

    assert repository.delete(uuid4()) is False