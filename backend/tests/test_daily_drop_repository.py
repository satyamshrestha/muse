from datetime import date, timedelta
from uuid import uuid4

from app.models.daily_drop import DailyDrop
from app.models.user import User
from app.repositories.daily_drop_repository import DailyDropRepository


def create_user(db):
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed_password",
        display_name="Daily Drop Tester",
    )
    db.add(user)
    db.flush()
    return user


def test_create_daily_drop(db):
    user = create_user(db)
    repository = DailyDropRepository(db)
    today = date.today()

    drop = repository.create(
        user_id=user.id,
        title="Daily Inspiration",
        content="Keep moving forward.",
        drop_date=today,
        source="system",
    )

    assert drop.id is not None
    assert drop.user_id == user.id
    assert drop.title == "Daily Inspiration"
    assert drop.content == "Keep moving forward."
    assert drop.drop_date == today
    assert drop.source == "system"


def test_get_by_id_returns_drop(db):
    user = create_user(db)
    repository = DailyDropRepository(db)

    created = repository.create(
        user_id=user.id,
        title="Test Drop",
        content="Test content",
        drop_date=date.today(),
        source="system",
    )

    result = repository.get_by_id(created.id)

    assert result is not None
    assert result.id == created.id


def test_get_by_id_returns_none_for_missing_drop(db):
    repository = DailyDropRepository(db)

    result = repository.get_by_id(uuid4())

    assert result is None


def test_get_for_user_returns_only_users_drops(db):
    user_one = create_user(db)
    user_two = create_user(db)
    repository = DailyDropRepository(db)

    first = repository.create(
        user_id=user_one.id,
        title="First Drop",
        content="First content",
        drop_date=date.today(),
        source="system",
    )

    repository.create(
        user_id=user_two.id,
        title="Other User Drop",
        content="Other content",
        drop_date=date.today(),
        source="system",
    )

    second = repository.create(
        user_id=user_one.id,
        title="Second Drop",
        content="Second content",
        drop_date=date.today() - timedelta(days=1),
        source="system",
    )

    results = repository.get_for_user(user_one.id)

    assert len(results) == 2
    assert {drop.id for drop in results} == {
        first.id,
        second.id,
    }


def test_get_by_date_returns_matching_drops(db):
    user = create_user(db)
    repository = DailyDropRepository(db)
    today = date.today()

    first = repository.create(
        user_id=user.id,
        title="First Drop",
        content="First content",
        drop_date=today,
        source="system",
    )

    repository.create(
        user_id=user.id,
        title="Yesterday Drop",
        content="Yesterday content",
        drop_date=today - timedelta(days=1),
        source="system",
    )

    second = repository.create(
        user_id=user.id,
        title="Second Drop",
        content="Second content",
        drop_date=today,
        source="community",
    )

    results = repository.get_by_date(user.id, today)

    assert len(results) == 2
    assert {drop.id for drop in results} == {
        first.id,
        second.id,
    }


def test_get_by_date_returns_empty_list_when_no_matches(db):
    user = create_user(db)
    repository = DailyDropRepository(db)

    results = repository.get_by_date(
        user.id,
        date.today() - timedelta(days=10),
    )

    assert results == []


def test_delete_daily_drop(db):
    user = create_user(db)
    repository = DailyDropRepository(db)

    drop = repository.create(
        user_id=user.id,
        title="Delete Me",
        content="Temporary content",
        drop_date=date.today(),
        source="system",
    )

    result = repository.delete(drop.id)

    assert result is True
    assert repository.get_by_id(drop.id) is None


def test_delete_returns_false_for_missing_drop(db):
    repository = DailyDropRepository(db)

    result = repository.delete(uuid4())

    assert result is False