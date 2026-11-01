from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.models.daily_drop import DailyDrop
from app.models.user import User
from app.services.daily_drop_service import DailyDropService


def create_user(db):
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed_password",
        display_name="Daily Drop Tester",
    )
    db.add(user)
    db.flush()
    return user


def create_drop(service, user_id, **overrides):
    data = {
        "title": "Daily Inspiration",
        "content": "Keep moving forward.",
        "drop_date": date.today(),
        "source": "system",
    }
    data.update(overrides)

    return service.create_drop(user_id=user_id, **data)


def test_create_daily_drop(db):
    user = create_user(db)
    service = DailyDropService(db)

    drop = create_drop(service, user.id)

    assert drop.id is not None
    assert drop.user_id == user.id
    assert drop.title == "Daily Inspiration"
    assert drop.content == "Keep moving forward."
    assert drop.drop_date == date.today()
    assert drop.source == "system"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("title", "", "Title cannot be empty"),
        ("title", "   ", "Title cannot be empty"),
        ("content", "", "Content cannot be empty"),
        ("content", "   ", "Content cannot be empty"),
        ("source", "", "Source cannot be empty"),
        ("source", "   ", "Source cannot be empty"),
        ("drop_date", None, "Drop date cannot be empty"),
    ],
)
def test_create_daily_drop_rejects_invalid_data(
    db,
    field,
    value,
    message,
):
    user = create_user(db)
    service = DailyDropService(db)

    with pytest.raises(ValueError, match=message):
        create_drop(service, user.id, **{field: value})


def test_get_drop_returns_owned_drop(db):
    user = create_user(db)
    service = DailyDropService(db)

    created = create_drop(service, user.id)

    result = service.get_drop(user.id, created.id)

    assert result is not None
    assert result.id == created.id


def test_get_drop_does_not_return_another_users_drop(db):
    owner = create_user(db)
    another_user = create_user(db)
    service = DailyDropService(db)

    created = create_drop(service, owner.id)

    result = service.get_drop(another_user.id, created.id)

    assert result is None


def test_get_drop_returns_none_for_unknown_id(db):
    user = create_user(db)
    service = DailyDropService(db)

    result = service.get_drop(user.id, uuid4())

    assert result is None


def test_get_user_drops_returns_only_users_drops(db):
    user_one = create_user(db)
    user_two = create_user(db)
    service = DailyDropService(db)

    first = create_drop(service, user_one.id, title="First Drop")

    create_drop(
        service,
        user_two.id,
        title="Another User Drop",
    )

    second = create_drop(
        service,
        user_one.id,
        title="Second Drop",
        drop_date=date.today() - timedelta(days=1),
    )

    results = service.get_user_drops(user_one.id)

    assert len(results) == 2
    assert {drop.id for drop in results} == {
        first.id,
        second.id,
    }


def test_get_drops_by_date_returns_matching_drops(db):
    user = create_user(db)
    service = DailyDropService(db)
    today = date.today()

    first = create_drop(service, user.id, title="First Drop")

    create_drop(
        service,
        user.id,
        title="Yesterday Drop",
        drop_date=today - timedelta(days=1),
    )

    second = create_drop(
        service,
        user.id,
        title="Second Drop",
        source="community",
    )

    results = service.get_drops_by_date(user.id, today)

    assert len(results) == 2
    assert {drop.id for drop in results} == {
        first.id,
        second.id,
    }


def test_get_drops_by_date_returns_empty_list(db):
    user = create_user(db)
    service = DailyDropService(db)

    results = service.get_drops_by_date(
        user.id,
        date.today() - timedelta(days=10),
    )

    assert results == []


def test_delete_daily_drop(db):
    user = create_user(db)
    service = DailyDropService(db)

    drop = create_drop(service, user.id)

    result = service.delete_drop(user.id, drop.id)

    assert result is True
    assert db.get(DailyDrop, drop.id) is None


def test_delete_does_not_allow_another_user_to_delete_drop(db):
    owner = create_user(db)
    another_user = create_user(db)
    service = DailyDropService(db)

    drop = create_drop(service, owner.id)

    with pytest.raises(ValueError, match="Daily drop not found"):
        service.delete_drop(another_user.id, drop.id)

    assert db.get(DailyDrop, drop.id) is not None


def test_delete_unknown_drop_raises_error(db):
    user = create_user(db)
    service = DailyDropService(db)

    with pytest.raises(ValueError, match="Daily drop not found"):
        service.delete_drop(user.id, uuid4())