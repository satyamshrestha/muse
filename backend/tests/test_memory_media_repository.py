from uuid import uuid4

from app.models.friend_group import FriendGroup
from app.models.group_membership import GroupMembership
from app.models.media import Media
from app.models.memory import Memory
from app.models.memory_media import MemoryMedia
from app.models.user import User
from app.repositories.memory_media_repository import (
    MemoryMediaRepository,
)


def create_test_user(db) -> User:
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed-password",
        display_name="Test User",
    )
    db.add(user)
    db.flush()
    return user


def create_test_memory(db, user: User) -> Memory:
    group = FriendGroup(name="Memory Media Test Group")
    db.add(group)
    db.flush()

    db.add(
        GroupMembership(
            user_id=user.id,
            group_id=group.id,
        )
    )
    db.flush()

    memory = Memory(
        group_id=group.id,
        created_by=user.id,
        title="Test Memory",
        description="Repository test memory",
    )
    db.add(memory)
    db.flush()
    return memory


def create_test_media(db, user: User) -> Media:
    media = Media(
        uploaded_by=user.id,
        object_key=f"test/{uuid4()}.jpg",
        media_type="image",
        mime_type="image/jpeg",
    )
    db.add(media)
    db.flush()
    return media


def test_memory_media_repository_create(db):
    user = create_test_user(db)
    memory = create_test_memory(db, user)
    media = create_test_media(db, user)

    repository = MemoryMediaRepository(db)
    link = repository.create(memory.id, media.id)
    db.commit()

    saved_link = db.query(MemoryMedia).filter(
        MemoryMedia.id == link.id
    ).first()

    assert saved_link is not None
    assert saved_link.memory_id == memory.id
    assert saved_link.media_id == media.id
    assert saved_link.created_at is not None


def test_memory_media_repository_get_by_id(db):
    user = create_test_user(db)
    memory = create_test_memory(db, user)
    media = create_test_media(db, user)

    repository = MemoryMediaRepository(db)
    link = repository.create(memory.id, media.id)
    db.flush()

    result = repository.get_by_id(link.id)

    assert result is not None
    assert result.id == link.id
    assert result.memory_id == memory.id
    assert result.media_id == media.id


def test_memory_media_repository_get_by_id_not_found(db):
    repository = MemoryMediaRepository(db)

    assert repository.get_by_id(uuid4()) is None


def test_memory_media_repository_get_by_memory_and_media(db):
    user = create_test_user(db)
    memory = create_test_memory(db, user)
    media = create_test_media(db, user)

    repository = MemoryMediaRepository(db)
    link = repository.create(memory.id, media.id)
    db.flush()

    result = repository.get_by_memory_and_media(
        memory.id,
        media.id,
    )

    assert result is not None
    assert result.id == link.id


def test_memory_media_repository_get_by_memory_and_media_not_found(db):
    user = create_test_user(db)
    memory = create_test_memory(db, user)
    media = create_test_media(db, user)

    repository = MemoryMediaRepository(db)

    assert repository.get_by_memory_and_media(
        memory.id,
        media.id,
    ) is None


def test_memory_media_repository_list_by_memory(db):
    user = create_test_user(db)
    memory = create_test_memory(db, user)
    other_memory = create_test_memory(db, user)

    first_media = create_test_media(db, user)
    second_media = create_test_media(db, user)
    other_media = create_test_media(db, user)

    repository = MemoryMediaRepository(db)
    first_link = repository.create(memory.id, first_media.id)
    second_link = repository.create(memory.id, second_media.id)
    repository.create(other_memory.id, other_media.id)
    db.flush()

    results = repository.list_by_memory(memory.id)

    assert len(results) == 2
    assert {link.id for link in results} == {
        first_link.id,
        second_link.id,
    }
    assert all(link.memory_id == memory.id for link in results)


def test_memory_media_repository_list_by_memory_empty(db):
    user = create_test_user(db)
    memory = create_test_memory(db, user)

    repository = MemoryMediaRepository(db)

    assert repository.list_by_memory(memory.id) == []


def test_memory_media_repository_list_by_memory_pagination(db):
    user = create_test_user(db)
    memory = create_test_memory(db, user)
    media_items = [
        create_test_media(db, user)
        for _ in range(3)
    ]

    repository = MemoryMediaRepository(db)
    for media in media_items:
        repository.create(memory.id, media.id)
    db.flush()

    first_page = repository.list_by_memory(
        memory.id,
        limit=2,
        offset=0,
    )
    second_page = repository.list_by_memory(
        memory.id,
        limit=2,
        offset=2,
    )

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert len({
        link.id for link in first_page + second_page
    }) == 3


def test_memory_media_repository_delete(db):
    user = create_test_user(db)
    memory = create_test_memory(db, user)
    media = create_test_media(db, user)

    repository = MemoryMediaRepository(db)
    link = repository.create(memory.id, media.id)
    db.flush()
    link_id = link.id

    repository.delete(link)
    db.flush()

    assert repository.get_by_id(link_id) is None