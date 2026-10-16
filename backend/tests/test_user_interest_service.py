from uuid import uuid4

import pytest

from app.models.user import User
from app.services.user_interest_service import (
    UserInterestService,
    UserInterestValidationError,
)


def create_user(db) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Interest Service Test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_replace_normalizes_and_deduplicates_interests(db):
    user = create_user(db)
    service = UserInterestService(db)

    records = service.replace_for_user(
        user.id,
        [" Programming ", "Music", "programming", "Travel"],
    )

    assert [record.interest for record in records] == [
        "Programming", "Music", "Travel"
    ]


@pytest.mark.parametrize(
    "interests",
    [
        [""],
        ["   "],
        ["x" * 101],
        ["Programming"] * 51,
    ],
)
def test_replace_rejects_invalid_interests(db, interests):
    user = create_user(db)
    service = UserInterestService(db)

    with pytest.raises(UserInterestValidationError):
        service.replace_for_user(user.id, interests)


def test_replace_with_empty_list_clears_interests(db):
    user = create_user(db)
    service = UserInterestService(db)

    service.replace_for_user(user.id, ["Programming", "Music"])
    result = service.replace_for_user(user.id, [])

    assert result == []
    assert service.get_for_user(user.id) == []


def test_get_interests_is_user_scoped(db):
    user = create_user(db)
    other_user = create_user(db)
    service = UserInterestService(db)

    service.replace_for_user(user.id, ["Programming"])
    service.replace_for_user(other_user.id, ["Cooking"])

    assert [
        record.interest for record in service.get_for_user(user.id)
    ] == ["Programming"]

    assert [
        record.interest
        for record in service.get_for_user(other_user.id)
    ] == ["Cooking"]


def test_invalid_replacement_preserves_existing_interests(db):
    user = create_user(db)
    service = UserInterestService(db)

    service.replace_for_user(user.id, ["Programming"])

    with pytest.raises(UserInterestValidationError):
        service.replace_for_user(user.id, ["", "Music"])

    assert [
        record.interest for record in service.get_for_user(user.id)
    ] == ["Programming"]