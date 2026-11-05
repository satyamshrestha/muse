from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models.media import Media
from app.models.memory import Memory
from app.models.memory_media import MemoryMedia
from app.models.friend_group import FriendGroup
from app.models.group_membership import GroupMembership
from app.models.user import User
from app.repositories.media_repository import MediaRepository


def create_test_user(db) -> User:
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed-password",
        display_name="Test User",
    )
    db.add(user)
    db.flush()
    return user


def create_test_media(
    db,
    user: User,
    object_key: str | None = None,
) -> Media:
    media = Media(
        uploaded_by=user.id,
        object_key=object_key or f"test/{uuid4()}.jpg",
        media_type="image",
        mime_type="image/jpeg",
    )
    db.add(media)
    db.flush()
    return media


def create_test_memory(db, user: User) -> Memory:
    group = FriendGroup(name=f"Media Test Group {uuid4()}")
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
        description="Media repository test memory",
    )
    db.add(memory)
    db.flush()
    return memory


def test_media_repository_create(db):
    user = create_test_user(db)
    repository = MediaRepository(db)

    object_key = f"test/{uuid4()}.jpg"

    media = repository.create(
        uploaded_by=user.id,
        object_key=object_key,
        media_type="image",
        mime_type="image/jpeg",
    )

    assert media.id is not None
    assert media.uploaded_by == user.id
    assert media.object_key == object_key
    assert media.media_type == "image"
    assert media.mime_type == "image/jpeg"


def test_media_repository_get_by_id(db):
    user = create_test_user(db)
    media = create_test_media(db, user)
    repository = MediaRepository(db)

    result = repository.get_by_id(media.id)

    assert result is not None
    assert result.id == media.id
    assert result.uploaded_by == user.id


def test_media_repository_get_by_id_not_found(db):
    repository = MediaRepository(db)

    assert repository.get_by_id(uuid4()) is None


def test_media_repository_get_by_id_for_user(db):
    user = create_test_user(db)
    media = create_test_media(db, user)
    repository = MediaRepository(db)

    result = repository.get_by_id_for_user(
        media_id=media.id,
        user_id=user.id,
    )

    assert result is not None
    assert result.id == media.id


def test_media_repository_get_by_id_for_different_user(db):
    uploader = create_test_user(db)
    another_user = create_test_user(db)
    media = create_test_media(db, uploader)
    repository = MediaRepository(db)

    result = repository.get_by_id_for_user(
        media_id=media.id,
        user_id=another_user.id,
    )

    assert result is None


def test_media_repository_get_by_id_for_user_not_found(db):
    user = create_test_user(db)
    repository = MediaRepository(db)

    assert repository.get_by_id_for_user(
        media_id=uuid4(),
        user_id=user.id,
    ) is None


def test_media_repository_list_by_user(db):
    user = create_test_user(db)
    another_user = create_test_user(db)

    first_media = create_test_media(db, user)
    second_media = create_test_media(db, user)
    create_test_media(db, another_user)

    repository = MediaRepository(db)

    results = repository.list_by_user(user.id)

    assert len(results) == 2
    assert {media.id for media in results} == {
        first_media.id,
        second_media.id,
    }
    assert all(media.uploaded_by == user.id for media in results)


def test_media_repository_list_by_user_empty(db):
    user = create_test_user(db)
    repository = MediaRepository(db)

    assert repository.list_by_user(user.id) == []


def test_media_repository_list_by_user_pagination(db):
    user = create_test_user(db)

    media_items = [
        create_test_media(db, user)
        for _ in range(3)
    ]

    repository = MediaRepository(db)

    first_page = repository.list_by_user(
        user_id=user.id,
        limit=2,
        offset=0,
    )
    second_page = repository.list_by_user(
        user_id=user.id,
        limit=2,
        offset=2,
    )

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert len({
        media.id for media in first_page + second_page
    }) == len(media_items)


def test_media_repository_list_by_user_newest_first(db):
    user = create_test_user(db)

    older_media = create_test_media(db, user)
    newer_media = create_test_media(db, user)

    now = datetime.now(timezone.utc)
    older_media.created_at = now - timedelta(days=1)
    newer_media.created_at = now

    db.flush()

    repository = MediaRepository(db)
    results = repository.list_by_user(user.id)

    assert [media.id for media in results] == [
        newer_media.id,
        older_media.id,
    ]


def test_media_repository_has_attachments_false(db):
    user = create_test_user(db)
    media = create_test_media(db, user)
    repository = MediaRepository(db)

    assert repository.has_attachments(media.id) is False


def test_media_repository_has_attachments_true(db):
    user = create_test_user(db)
    media = create_test_media(db, user)
    memory = create_test_memory(db, user)

    db.add(
        MemoryMedia(
            memory_id=memory.id,
            media_id=media.id,
        )
    )
    db.flush()

    repository = MediaRepository(db)

    assert repository.has_attachments(media.id) is True


def test_media_repository_delete(db):
    user = create_test_user(db)
    media = create_test_media(db, user)
    repository = MediaRepository(db)

    media_id = media.id

    repository.delete(media)

    assert repository.get_by_id(media_id) is None