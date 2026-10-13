from uuid import uuid4

from app.models.device import Device
from app.models.user import User
from app.repositories.device_repository import DeviceRepository


def create_user(db) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Device Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_create_device(db):
    user = create_user(db)
    repository = DeviceRepository(db)

    device = repository.create(
        user_id=user.id,
        device_token="token-create-001",
        platform="android",
    )
    db.commit()

    assert device.id is not None
    assert device.user_id == user.id
    assert device.device_token == "token-create-001"
    assert device.platform == "android"


def test_get_by_token(db):
    user = create_user(db)
    repository = DeviceRepository(db)

    created = repository.create(
        user_id=user.id,
        device_token="token-lookup-001",
        platform="ios",
    )
    db.commit()

    found = repository.get_by_token("token-lookup-001")

    assert found is not None
    assert found.id == created.id


def test_get_by_id_requires_matching_owner(db):
    owner = create_user(db)
    other_user = create_user(db)
    repository = DeviceRepository(db)

    device = repository.create(
        user_id=owner.id,
        device_token="token-owner-001",
        platform="android",
    )
    db.commit()

    assert (
        repository.get_by_id_for_user(device.id, owner.id)
        is not None
    )
    assert (
        repository.get_by_id_for_user(device.id, other_user.id)
        is None
    )


def test_list_by_user_returns_only_that_users_devices(db):
    owner = create_user(db)
    other_user = create_user(db)
    repository = DeviceRepository(db)

    repository.create(
        user_id=owner.id,
        device_token="token-list-001",
        platform="android",
    )
    repository.create(
        user_id=owner.id,
        device_token="token-list-002",
        platform="ios",
    )
    repository.create(
        user_id=other_user.id,
        device_token="token-list-other",
        platform="android",
    )
    db.commit()

    devices = repository.list_by_user(owner.id)

    assert len(devices) == 2
    assert {device.user_id for device in devices} == {owner.id}
    assert {
        device.device_token for device in devices
    } == {"token-list-001", "token-list-002"}


def test_update_platform(db):
    user = create_user(db)
    repository = DeviceRepository(db)

    device = repository.create(
        user_id=user.id,
        device_token="token-update-001",
        platform="android",
    )
    db.commit()

    repository.update_platform(device, "ios")
    db.commit()
    db.refresh(device)

    assert device.platform == "ios"


def test_delete_device(db):
    user = create_user(db)
    repository = DeviceRepository(db)

    device = repository.create(
        user_id=user.id,
        device_token="token-delete-001",
        platform="android",
    )
    device_id = device.id
    db.commit()

    repository.delete(device)
    db.commit()

    assert repository.get_by_token("token-delete-001") is None
    assert repository.get_by_id_for_user(device_id, user.id) is None