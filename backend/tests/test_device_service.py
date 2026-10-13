from uuid import uuid4

import pytest

from app.models.device import Device
from app.models.user import User
from app.repositories.device_repository import DeviceRepository
from app.services.device_service import (
    DeviceNotFoundError,
    DeviceService,
    DeviceTokenConflictError,
)


def create_user(db) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Device Service Test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def build_service(db) -> DeviceService:
    return DeviceService(DeviceRepository(db))


def test_register_creates_device(db):
    user = create_user(db)
    service = build_service(db)

    device = service.register(
        user_id=user.id,
        device_token="service-register-001",
        platform="android",
    )

    assert device.id is not None
    assert device.user_id == user.id
    assert device.device_token == "service-register-001"
    assert device.platform == "android"


def test_register_same_token_for_same_user_is_idempotent(db):
    user = create_user(db)
    service = build_service(db)

    first = service.register(
        user_id=user.id,
        device_token="service-idempotent-001",
        platform="android",
    )
    second = service.register(
        user_id=user.id,
        device_token="service-idempotent-001",
        platform="android",
    )

    assert first.id == second.id
    assert len(service.list_for_user(user.id)) == 1


def test_register_same_token_updates_platform_for_same_user(db):
    user = create_user(db)
    service = build_service(db)

    first = service.register(
        user_id=user.id,
        device_token="service-platform-001",
        platform="android",
    )
    second = service.register(
        user_id=user.id,
        device_token="service-platform-001",
        platform="ios",
    )

    assert second.id == first.id
    assert second.platform == "ios"
    assert len(service.list_for_user(user.id)) == 1


def test_register_rejects_token_owned_by_another_user(db):
    owner = create_user(db)
    other_user = create_user(db)
    service = build_service(db)

    original = service.register(
        user_id=owner.id,
        device_token="service-conflict-001",
        platform="android",
    )

    with pytest.raises(DeviceTokenConflictError):
        service.register(
            user_id=other_user.id,
            device_token="service-conflict-001",
            platform="ios",
        )

    db.refresh(original)
    assert original.user_id == owner.id
    assert original.platform == "android"
    assert service.list_for_user(other_user.id) == []


def test_update_platform_requires_device_ownership(db):
    owner = create_user(db)
    other_user = create_user(db)
    service = build_service(db)

    device = service.register(
        user_id=owner.id,
        device_token="service-owner-001",
        platform="android",
    )

    with pytest.raises(DeviceNotFoundError):
        service.update_platform(
            user_id=other_user.id,
            device_id=device.id,
            platform="ios",
        )

    db.refresh(device)
    assert device.platform == "android"


def test_unregister_requires_device_ownership(db):
    owner = create_user(db)
    other_user = create_user(db)
    service = build_service(db)

    device = service.register(
        user_id=owner.id,
        device_token="service-delete-001",
        platform="android",
    )

    with pytest.raises(DeviceNotFoundError):
        service.unregister(
            user_id=other_user.id,
            device_id=device.id,
        )

    assert service.list_for_user(owner.id)[0].id == device.id


def test_unregister_removes_owned_device(db):
    user = create_user(db)
    service = build_service(db)

    device = service.register(
        user_id=user.id,
        device_token="service-delete-002",
        platform="android",
    )

    service.unregister(
        user_id=user.id,
        device_id=device.id,
    )

    assert service.list_for_user(user.id) == []