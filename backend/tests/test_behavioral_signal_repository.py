from uuid import uuid4

from app.models.behavioral_signal import BehavioralSignal
from app.models.user import User
from app.repositories.behavioral_signal_repository import (
    BehavioralSignalRepository,
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


def test_create_behavioral_signal(db):
    user = create_user(db)
    repository = BehavioralSignalRepository(db)

    signal = repository.create(
        user_id=user.id,
        signal_type="mood",
        value="happy",
    )

    assert signal.id is not None
    assert signal.user_id == user.id
    assert signal.signal_type == "mood"
    assert signal.value == "happy"


def test_get_by_id_returns_signal(db):
    user = create_user(db)
    repository = BehavioralSignalRepository(db)

    created = repository.create(
        user_id=user.id,
        signal_type="activity",
        value="completed_task",
    )

    result = repository.get_by_id(created.id)

    assert result is not None
    assert result.id == created.id


def test_get_by_id_returns_none_for_missing_signal(db):
    repository = BehavioralSignalRepository(db)

    result = repository.get_by_id(uuid4())

    assert result is None


def test_get_for_user_returns_only_users_signals(db):
    user_one = create_user(db)
    user_two = create_user(db)
    repository = BehavioralSignalRepository(db)

    first = repository.create(
        user_id=user_one.id,
        signal_type="mood",
        value="happy",
    )
    repository.create(
        user_id=user_two.id,
        signal_type="mood",
        value="calm",
    )
    second = repository.create(
        user_id=user_one.id,
        signal_type="activity",
        value="studied",
    )

    results = repository.get_for_user(user_one.id)

    assert len(results) == 2
    assert {signal.id for signal in results} == {
        first.id,
        second.id,
    }


def test_get_by_type_returns_matching_signals(db):
    user = create_user(db)
    repository = BehavioralSignalRepository(db)

    mood_signal = repository.create(
        user_id=user.id,
        signal_type="mood",
        value="happy",
    )
    repository.create(
        user_id=user.id,
        signal_type="activity",
        value="studied",
    )
    another_mood = repository.create(
        user_id=user.id,
        signal_type="mood",
        value="calm",
    )

    results = repository.get_by_type(user.id, "mood")

    assert len(results) == 2
    assert {signal.id for signal in results} == {
        mood_signal.id,
        another_mood.id,
    }


def test_get_by_type_returns_empty_list_when_no_matches(db):
    user = create_user(db)
    repository = BehavioralSignalRepository(db)

    results = repository.get_by_type(user.id, "nonexistent")

    assert results == []


def test_delete_behavioral_signal(db):
    user = create_user(db)
    repository = BehavioralSignalRepository(db)

    signal = repository.create(
        user_id=user.id,
        signal_type="mood",
        value="happy",
    )

    result = repository.delete(signal.id)

    assert result is True
    assert repository.get_by_id(signal.id) is None


def test_delete_returns_false_for_missing_signal(db):
    repository = BehavioralSignalRepository(db)

    result = repository.delete(uuid4())

    assert result is False