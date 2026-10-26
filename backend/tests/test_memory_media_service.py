from uuid import uuid4

import pytest

from app.models.friend_group import FriendGroup
from app.models.group_membership import GroupMembership
from app.models.media import Media
from app.models.memory import Memory
from app.models.memory_media import MemoryMedia
from app.models.user import User
from app.services.memory_media_service import MemoryMediaService


def create_test_user(db) -> User:
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed-password",
        display_name="Test User",
    )
    db.add(user)
    db.flush()
    return user


def create_test_group(db, *users: User) -> FriendGroup:
    group = FriendGroup(name="Memory Media Service Group")
    db.add(group)
    db.flush()

    for user in users:
        db.add(
            GroupMembership(
                user_id=user.id,
                group_id=group.id,
            )
        )

    db.flush()
    return group


def create_test_memory(
    db,
    group: FriendGroup,
    creator: User,
) -> Memory:
    memory = Memory(
        group_id=group.id,
        created_by=creator.id,
        title="Service Test Memory",
        description="Memory media service test",
    )
    db.add(memory)
    db.flush()
    return memory


def create_test_media(db, uploader: User) -> Media:
    media = Media(
        uploaded_by=uploader.id,
        object_key=f"service-tests/{uuid4()}.jpg",
        media_type="image",
        mime_type="image/jpeg",
    )
    db.add(media)
    db.flush()
    return media


def test_attach_media_to_memory(db):
    user = create_test_user(db)
    group = create_test_group(db, user)
    memory = create_test_memory(db, group, user)
    media = create_test_media(db, user)

    service = MemoryMediaService(db)
    link = service.attach_media(
        group_id=group.id,
        memory_id=memory.id,
        media_id=media.id,
        user_id=user.id,
    )

    assert link.id is not None
    assert link.memory_id == memory.id
    assert link.media_id == media.id


def test_attach_media_rejects_non_member(db):
    owner = create_test_user(db)
    outsider = create_test_user(db)
    group = create_test_group(db, owner)
    memory = create_test_memory(db, group, owner)
    media = create_test_media(db, outsider)

    service = MemoryMediaService(db)

    with pytest.raises(ValueError, match="not a member"):
        service.attach_media(
            group.id, memory.id, media.id, outsider.id
        )


def test_attach_media_rejects_missing_group(db):
    user = create_test_user(db)
    service = MemoryMediaService(db)

    with pytest.raises(ValueError, match="Group not found"):
        service.attach_media(
            uuid4(), uuid4(), uuid4(), user.id
        )


def test_attach_media_rejects_memory_from_another_group(db):
    user = create_test_user(db)
    first_group = create_test_group(db, user)
    second_group = create_test_group(db, user)
    memory = create_test_memory(db, second_group, user)
    media = create_test_media(db, user)

    service = MemoryMediaService(db)

    with pytest.raises(ValueError, match="Memory not found"):
        service.attach_media(
            first_group.id, memory.id, media.id, user.id
        )


def test_attach_media_rejects_missing_media(db):
    user = create_test_user(db)
    group = create_test_group(db, user)
    memory = create_test_memory(db, group, user)
    service = MemoryMediaService(db)

    with pytest.raises(ValueError, match="Media not found"):
        service.attach_media(
            group.id, memory.id, uuid4(), user.id
        )


def test_attach_media_rejects_another_users_media(db):
    owner = create_test_user(db)
    uploader = create_test_user(db)
    group = create_test_group(db, owner, uploader)
    memory = create_test_memory(db, group, owner)
    media = create_test_media(db, uploader)

    service = MemoryMediaService(db)

    with pytest.raises(ValueError, match="media uploader"):
        service.attach_media(
            group.id, memory.id, media.id, owner.id
        )


def test_attach_media_rejects_duplicate_link(db):
    user = create_test_user(db)
    group = create_test_group(db, user)
    memory = create_test_memory(db, group, user)
    media = create_test_media(db, user)
    service = MemoryMediaService(db)

    service.attach_media(group.id, memory.id, media.id, user.id)

    with pytest.raises(ValueError, match="already attached"):
        service.attach_media(
            group.id, memory.id, media.id, user.id
        )


def test_list_memory_media_returns_only_requested_memory_links(db):
    user = create_test_user(db)
    group = create_test_group(db, user)
    memory = create_test_memory(db, group, user)
    other_memory = create_test_memory(db, group, user)
    first_media = create_test_media(db, user)
    second_media = create_test_media(db, user)
    other_media = create_test_media(db, user)

    service = MemoryMediaService(db)
    first_link = service.attach_media(
        group.id, memory.id, first_media.id, user.id
    )
    second_link = service.attach_media(
        group.id, memory.id, second_media.id, user.id
    )
    service.attach_media(
        group.id, other_memory.id, other_media.id, user.id
    )

    results = service.list_memory_media(
        group.id, memory.id, user.id
    )

    assert {link.id for link in results} == {
        first_link.id,
        second_link.id,
    }


def test_list_memory_media_rejects_invalid_limit(db):
    user = create_test_user(db)
    group = create_test_group(db, user)
    memory = create_test_memory(db, group, user)
    service = MemoryMediaService(db)

    with pytest.raises(ValueError, match="Limit must be"):
        service.list_memory_media(
            group.id, memory.id, user.id, limit=0
        )


def test_list_memory_media_rejects_negative_offset(db):
    user = create_test_user(db)
    group = create_test_group(db, user)
    memory = create_test_memory(db, group, user)
    service = MemoryMediaService(db)

    with pytest.raises(ValueError, match="Offset cannot"):
        service.list_memory_media(
            group.id, memory.id, user.id, offset=-1
        )


def test_detach_media_by_memory_creator(db):
    user = create_test_user(db)
    group = create_test_group(db, user)
    memory = create_test_memory(db, group, user)
    media = create_test_media(db, user)
    service = MemoryMediaService(db)

    link = service.attach_media(
        group.id, memory.id, media.id, user.id
    )

    result = service.detach_media(
        group.id, memory.id, link.id, user.id
    )

    assert result is True
    assert db.get(MemoryMedia, link.id) is None


def test_detach_media_rejects_non_creator(db):
    creator = create_test_user(db)
    member = create_test_user(db)
    group = create_test_group(db, creator, member)
    memory = create_test_memory(db, group, creator)
    media = create_test_media(db, creator)
    service = MemoryMediaService(db)

    link = service.attach_media(
        group.id, memory.id, media.id, creator.id
    )

    with pytest.raises(ValueError, match="memory creator"):
        service.detach_media(
            group.id, memory.id, link.id, member.id
        )


def test_detach_media_rejects_link_from_another_memory(db):
    user = create_test_user(db)
    group = create_test_group(db, user)
    first_memory = create_test_memory(db, group, user)
    second_memory = create_test_memory(db, group, user)
    media = create_test_media(db, user)
    service = MemoryMediaService(db)

    link = service.attach_media(
        group.id, first_memory.id, media.id, user.id
    )

    with pytest.raises(ValueError, match="link not found"):
        service.detach_media(
            group.id, second_memory.id, link.id, user.id
        )


def test_detach_media_rejects_missing_link(db):
    user = create_test_user(db)
    group = create_test_group(db, user)
    memory = create_test_memory(db, group, user)
    service = MemoryMediaService(db)

    with pytest.raises(ValueError, match="link not found"):
        service.detach_media(
            group.id, memory.id, uuid4(), user.id
        )