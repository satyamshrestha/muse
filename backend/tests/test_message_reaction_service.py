from uuid import uuid4

import pytest

from app.models.friend_group import FriendGroup
from app.models.group_membership import GroupMembership
from app.models.message_reaction import MessageReaction
from app.models.room_message import RoomMessage
from app.models.user import User
from app.services.message_reaction_service import MessageReactionService


def create_test_user(db, display_name="Reaction Tester"):
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="test-hash",
        display_name=display_name,
    )
    db.add(user)
    db.flush()
    return user


def create_test_message(db, user):
    group = FriendGroup(name=f"Reaction Group {uuid4()}")
    db.add(group)
    db.flush()

    db.add(
        GroupMembership(
            user_id=user.id,
            group_id=group.id,
        )
    )

    message = RoomMessage(
        group_id=group.id,
        user_id=user.id,
        content="Test room message",
    )
    db.add(message)
    db.flush()

    return group, message


def add_member(db, user, group):
    db.add(
        GroupMembership(
            user_id=user.id,
            group_id=group.id,
        )
    )
    db.flush()


def test_create_reaction_successfully(db):
    user = create_test_user(db)
    _, message = create_test_message(db, user)
    service = MessageReactionService(db)

    result = service.create_reaction(
        message_id=message.id,
        user_id=user.id,
        reaction="👍",
    )

    assert result.id is not None
    assert result.message_id == message.id
    assert result.user_id == user.id
    assert result.reaction == "👍"


def test_create_reaction_rejects_missing_message(db):
    user = create_test_user(db)
    service = MessageReactionService(db)

    with pytest.raises(ValueError, match="Room message not found"):
        service.create_reaction(
            message_id=uuid4(),
            user_id=user.id,
            reaction="👍",
        )


def test_create_reaction_rejects_non_member(db):
    owner = create_test_user(db, "Message Owner")
    outsider = create_test_user(db, "Outsider")
    _, message = create_test_message(db, owner)
    service = MessageReactionService(db)

    with pytest.raises(ValueError, match="not a member"):
        service.create_reaction(
            message_id=message.id,
            user_id=outsider.id,
            reaction="👍",
        )


def test_create_reaction_rejects_duplicate(db):
    user = create_test_user(db)
    _, message = create_test_message(db, user)
    service = MessageReactionService(db)

    service.create_reaction(message.id, user.id, "👍")

    with pytest.raises(ValueError, match="already reacted"):
        service.create_reaction(message.id, user.id, "😂")


def test_create_reaction_rejects_empty_reaction(db):
    user = create_test_user(db)
    _, message = create_test_message(db, user)
    service = MessageReactionService(db)

    with pytest.raises(ValueError, match="must not be empty"):
        service.create_reaction(message.id, user.id, "   ")


def test_get_message_reactions_successfully(db):
    first_user = create_test_user(db, "First User")
    group, message = create_test_message(db, first_user)
    second_user = create_test_user(db, "Second User")
    add_member(db, second_user, group)

    service = MessageReactionService(db)
    first = service.create_reaction(message.id, first_user.id, "👍")
    second = service.create_reaction(message.id, second_user.id, "❤️")

    results = service.get_message_reactions(message.id, first_user.id)

    assert {item.id for item in results} == {first.id, second.id}


def test_get_message_reactions_rejects_non_member(db):
    owner = create_test_user(db, "Message Owner")
    outsider = create_test_user(db, "Outsider")
    _, message = create_test_message(db, owner)
    service = MessageReactionService(db)

    with pytest.raises(ValueError, match="not a member"):
        service.get_message_reactions(message.id, outsider.id)


def test_update_reaction_successfully(db):
    user = create_test_user(db)
    _, message = create_test_message(db, user)
    service = MessageReactionService(db)
    created = service.create_reaction(message.id, user.id, "👍")

    updated = service.update_reaction(
        reaction_id=created.id,
        user_id=user.id,
        reaction="🎉",
    )

    assert updated.id == created.id
    assert updated.reaction == "🎉"


def test_update_reaction_rejects_missing_reaction(db):
    user = create_test_user(db)
    service = MessageReactionService(db)

    with pytest.raises(ValueError, match="Message reaction not found"):
        service.update_reaction(uuid4(), user.id, "🎉")


def test_update_reaction_rejects_another_users_reaction(db):
    owner = create_test_user(db, "Reaction Owner")
    other_user = create_test_user(db, "Other User")
    _, message = create_test_message(db, owner)
    service = MessageReactionService(db)
    created = service.create_reaction(message.id, owner.id, "👍")

    with pytest.raises(ValueError, match="Only the reaction creator"):
        service.update_reaction(created.id, other_user.id, "🎉")


def test_update_reaction_rejects_empty_reaction(db):
    user = create_test_user(db)
    _, message = create_test_message(db, user)
    service = MessageReactionService(db)
    created = service.create_reaction(message.id, user.id, "👍")

    with pytest.raises(ValueError, match="must not be empty"):
        service.update_reaction(created.id, user.id, " ")


def test_delete_reaction_successfully(db):
    user = create_test_user(db)
    _, message = create_test_message(db, user)
    service = MessageReactionService(db)
    created = service.create_reaction(message.id, user.id, "👍")

    result = service.delete_reaction(created.id, user.id)

    assert result is True
    assert db.get(MessageReaction, created.id) is None


def test_delete_reaction_rejects_missing_reaction(db):
    user = create_test_user(db)
    service = MessageReactionService(db)

    with pytest.raises(ValueError, match="Message reaction not found"):
        service.delete_reaction(uuid4(), user.id)


def test_delete_reaction_rejects_another_users_reaction(db):
    owner = create_test_user(db, "Reaction Owner")
    other_user = create_test_user(db, "Other User")
    _, message = create_test_message(db, owner)
    service = MessageReactionService(db)
    created = service.create_reaction(message.id, owner.id, "👍")

    with pytest.raises(ValueError, match="Only the reaction creator"):
        service.delete_reaction(created.id, other_user.id)