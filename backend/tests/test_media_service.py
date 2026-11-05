from uuid import uuid4

import pytest

from app.models.friend_group import FriendGroup
from app.models.group_membership import GroupMembership
from app.models.media import Media
from app.models.memory import Memory
from app.models.memory_media import MemoryMedia
from app.models.user import User
from app.services.media_service import MediaService


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
    group = FriendGroup(name=f"Media Service Group {uuid4()}")
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
        description="Media service test memory",
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


def test_media_service_register_media(db):
    user = create_test_user(db)
    service = MediaService(db)

    media = service.register_media(
        user_id=user.id,
        object_key="uploads/test-image.jpg",
        media_type="image",
        mime_type="image/jpeg",
    )

    assert media.id is not None
    assert media.uploaded_by == user.id
    assert media.object_key == "uploads/test-image.jpg"
    assert media.media_type == "image"
    assert media.mime_type == "image/jpeg"
    assert media.created_at is not None


@pytest.mark.parametrize(
    ("object_key", "media_type", "mime_type", "message"),
    [
        ("", "image", "image/jpeg", "Object key cannot be empty"),
        ("   ", "image", "image/jpeg", "Object key cannot be empty"),
        ("a" * 501, "image", "image/jpeg",
         "Object key cannot exceed 500 characters"),
        ("uploads/image.jpg", "", "image/jpeg",
         "Media type cannot be empty"),
        ("uploads/image.jpg", "   ", "image/jpeg",
         "Media type cannot be empty"),
        ("uploads/image.jpg", "a" * 51, "image/jpeg",
         "Media type cannot exceed 50 characters"),
        ("uploads/image.jpg", "image", "",
         "MIME type cannot be empty"),
        ("uploads/image.jpg", "image", "   ",
         "MIME type cannot be empty"),
        ("uploads/image.jpg", "image", "a" * 101,
         "MIME type cannot exceed 100 characters"),
    ],
)
def test_media_service_register_media_validation(
    db,
    object_key,
    media_type,
    mime_type,
    message,
):
    user = create_test_user(db)
    service = MediaService(db)

    with pytest.raises(ValueError, match=message):
        service.register_media(
            user_id=user.id,
            object_key=object_key,
            media_type=media_type,
            mime_type=mime_type,
        )


def test_media_service_register_media_strips_metadata(db):
    user = create_test_user(db)
    service = MediaService(db)

    object_key = f"uploads/{uuid4()}.jpg"

    media = service.register_media(
        user_id=user.id,
        object_key=f" {object_key} ",
        media_type=" image ",
        mime_type=" image/jpeg ",
    )

    assert media.object_key == object_key
    assert media.media_type == "image"
    assert media.mime_type == "image/jpeg"


def test_media_service_get_media(db):
    user = create_test_user(db)
    media = create_test_media(db, user)
    service = MediaService(db)

    result = service.get_media(
        media_id=media.id,
        user_id=user.id,
    )

    assert result.id == media.id
    assert result.uploaded_by == user.id


def test_media_service_get_media_not_found(db):
    user = create_test_user(db)
    service = MediaService(db)

    with pytest.raises(ValueError, match="Media not found"):
        service.get_media(
            media_id=uuid4(),
            user_id=user.id,
        )


def test_media_service_get_media_forbidden_for_other_user(db):
    uploader = create_test_user(db)
    another_user = create_test_user(db)
    media = create_test_media(db, uploader)
    service = MediaService(db)

    with pytest.raises(ValueError, match="Media not found"):
        service.get_media(
            media_id=media.id,
            user_id=another_user.id,
        )


def test_media_service_list_media(db):
    user = create_test_user(db)
    another_user = create_test_user(db)

    first_media = create_test_media(db, user)
    second_media = create_test_media(db, user)
    create_test_media(db, another_user)

    service = MediaService(db)
    results = service.list_media(user_id=user.id)

    assert len(results) == 2
    assert {media.id for media in results} == {
        first_media.id,
        second_media.id,
    }
    assert all(media.uploaded_by == user.id for media in results)


def test_media_service_list_media_empty(db):
    user = create_test_user(db)
    service = MediaService(db)

    assert service.list_media(user_id=user.id) == []


def test_media_service_list_media_pagination(db):
    user = create_test_user(db)

    for _ in range(3):
        create_test_media(db, user)

    service = MediaService(db)

    first_page = service.list_media(
        user_id=user.id,
        limit=2,
        offset=0,
    )
    second_page = service.list_media(
        user_id=user.id,
        limit=2,
        offset=2,
    )

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert len({
        media.id for media in first_page + second_page
    }) == 3


@pytest.mark.parametrize("limit", [0, -1, 101])
def test_media_service_list_media_invalid_limit(db, limit):
    user = create_test_user(db)
    service = MediaService(db)

    with pytest.raises(
        ValueError,
        match="Limit must be between 1 and 100",
    ):
        service.list_media(
            user_id=user.id,
            limit=limit,
        )


def test_media_service_list_media_negative_offset(db):
    user = create_test_user(db)
    service = MediaService(db)

    with pytest.raises(
        ValueError,
        match="Offset cannot be negative",
    ):
        service.list_media(
            user_id=user.id,
            offset=-1,
        )


def test_media_service_delete_media(db):
    user = create_test_user(db)
    media = create_test_media(db, user)
    media_id = media.id

    service = MediaService(db)

    assert service.delete_media(
        media_id=media_id,
        user_id=user.id,
    ) is True

    assert db.get(Media, media_id) is None


def test_media_service_delete_media_not_found(db):
    user = create_test_user(db)
    service = MediaService(db)

    with pytest.raises(ValueError, match="Media not found"):
        service.delete_media(
            media_id=uuid4(),
            user_id=user.id,
        )


def test_media_service_delete_media_forbidden_for_other_user(db):
    uploader = create_test_user(db)
    another_user = create_test_user(db)
    media = create_test_media(db, uploader)
    service = MediaService(db)

    with pytest.raises(ValueError, match="Media not found"):
        service.delete_media(
            media_id=media.id,
            user_id=another_user.id,
        )

    assert db.get(Media, media.id) is not None


def test_media_service_delete_media_with_attachments(db):
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

    service = MediaService(db)

    with pytest.raises(
        ValueError,
        match="Cannot delete media while it is attached to memories",
    ):
        service.delete_media(
            media_id=media.id,
            user_id=user.id,
        )

    assert db.get(Media, media.id) is not None