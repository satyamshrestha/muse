from uuid import uuid4

from app.models.notification import Notification
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository


def create_user(db) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Notification Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_notification(
    repository: NotificationRepository,
    user_id,
    token: str,
) -> Notification:
    return repository.create(
        user_id=user_id,
        notification_type="group_activity",
        title=f"Notification {token}",
        body="Test notification body",
    )


def test_create_notification(db):
    user = create_user(db)
    repository = NotificationRepository(db)

    notification = create_notification(repository, user.id, "create")
    db.commit()
    db.refresh(notification)

    assert notification.id is not None
    assert notification.user_id == user.id
    assert notification.notification_type == "group_activity"
    assert notification.read_at is None


def test_get_by_id_requires_matching_owner(db):
    owner = create_user(db)
    other_user = create_user(db)
    repository = NotificationRepository(db)

    notification = create_notification(repository, owner.id, "owner")
    db.commit()

    assert repository.get_by_id_for_user(notification.id, owner.id) is not None
    assert repository.get_by_id_for_user(notification.id, other_user.id) is None


def test_list_by_user_only_returns_owned_notifications(db):
    owner = create_user(db)
    other_user = create_user(db)
    repository = NotificationRepository(db)

    create_notification(repository, owner.id, "first")
    create_notification(repository, owner.id, "second")
    create_notification(repository, other_user.id, "other")
    db.commit()

    notifications = repository.list_by_user(owner.id)

    assert len(notifications) == 2
    assert all(item.user_id == owner.id for item in notifications)


def test_list_supports_pagination(db):
    user = create_user(db)
    repository = NotificationRepository(db)

    for token in ("one", "two", "three"):
        create_notification(repository, user.id, token)
    db.commit()

    first_page = repository.list_by_user(user.id, limit=2, offset=0)
    second_page = repository.list_by_user(user.id, limit=2, offset=2)

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert first_page[0].id != first_page[1].id
    assert first_page[0].id != second_page[0].id


def test_unread_count_and_filter(db):
    user = create_user(db)
    repository = NotificationRepository(db)

    first = create_notification(repository, user.id, "unread-one")
    create_notification(repository, user.id, "unread-two")
    db.commit()

    repository.mark_read(first)
    db.commit()

    assert repository.count_unread(user.id) == 1
    unread = repository.list_by_user(user.id, unread_only=True)

    assert len(unread) == 1
    assert unread[0].read_at is None


def test_mark_read_is_idempotent(db):
    user = create_user(db)
    repository = NotificationRepository(db)

    notification = create_notification(repository, user.id, "read")
    db.commit()

    repository.mark_read(notification)
    db.commit()
    first_read_at = notification.read_at

    repository.mark_read(notification)
    db.commit()

    assert notification.read_at == first_read_at


def test_mark_all_read_only_affects_owned_unread_notifications(db):
    user = create_user(db)
    other_user = create_user(db)
    repository = NotificationRepository(db)

    create_notification(repository, user.id, "bulk-one")
    create_notification(repository, user.id, "bulk-two")
    other_notification = create_notification(
        repository,
        other_user.id,
        "bulk-other",
    )
    db.commit()

    updated_count = repository.mark_all_read(user.id)
    db.commit()

    assert updated_count == 2
    assert repository.count_unread(user.id) == 0
    assert repository.get_by_id_for_user(
        other_notification.id,
        other_user.id,
    ).read_at is None