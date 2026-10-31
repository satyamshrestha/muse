from uuid import uuid4

import pytest

from app.models.user import User
from app.services.behavioral_signal_service import (
    BehavioralSignalService,
)


def create_user(db):
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed_password",
        display_name="Signal Tester",
    )
    db.add(user)
    db.flush()
    return user


def test_create_signal(db):
    user = create_user(db)
    service = BehavioralSignalService(db)

    signal = service.create_signal(user.id, "mood", "happy")

    assert signal.user_id == user.id
    assert signal.signal_type == "mood"
    assert signal.value == "happy"


@pytest.mark.parametrize(
    ("signal_type", "value"),
    [
        ("", "happy"),
        ("   ", "happy"),
        ("mood", ""),
        ("mood", "   "),
    ],
)
def test_create_signal_rejects_empty_fields(db, signal_type, value):
    user = create_user(db)
    service = BehavioralSignalService(db)

    with pytest.raises(ValueError):
        service.create_signal(user.id, signal_type, value)


def test_get_user_signals(db):
    user = create_user(db)
    service = BehavioralSignalService(db)

    service.create_signal(user.id, "mood", "happy")
    service.create_signal(user.id, "activity", "studied")

    results = service.get_user_signals(user.id)

    assert len(results) == 2


def test_get_user_signals_by_type(db):
    user = create_user(db)
    service = BehavioralSignalService(db)

    service.create_signal(user.id, "mood", "happy")
    service.create_signal(user.id, "activity", "studied")
    service.create_signal(user.id, "mood", "calm")

    results = service.get_user_signals_by_type(user.id, "mood")

    assert len(results) == 2
    assert all(signal.signal_type == "mood" for signal in results)


def test_get_user_signals_by_type_rejects_empty_type(db):
    user = create_user(db)
    service = BehavioralSignalService(db)

    with pytest.raises(ValueError, match="Signal type must not be empty"):
        service.get_user_signals_by_type(user.id, "   ")


def test_delete_signal(db):
    user = create_user(db)
    service = BehavioralSignalService(db)

    signal = service.create_signal(user.id, "mood", "happy")

    result = service.delete_signal(signal.id, user.id)

    assert result is True
    assert service.get_user_signals(user.id) == []


def test_delete_signal_rejects_another_users_signal(db):
    owner = create_user(db)
    another_user = create_user(db)
    service = BehavioralSignalService(db)

    signal = service.create_signal(owner.id, "mood", "happy")

    with pytest.raises(
        ValueError,
        match="Cannot delete another user's signal",
    ):
        service.delete_signal(signal.id, another_user.id)


def test_delete_signal_rejects_missing_signal(db):
    user = create_user(db)
    service = BehavioralSignalService(db)

    with pytest.raises(ValueError, match="Behavioral signal not found"):
        service.delete_signal(uuid4(), user.id)