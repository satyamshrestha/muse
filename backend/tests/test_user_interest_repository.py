from uuid import uuid4

from app.models.user import User
from app.repositories.user_interest_repository import (
    UserInterestRepository,
)


def create_user(db) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Interest Repository Test",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_replace_and_get_interests(db):
    user = create_user(db)
    repository = UserInterestRepository(db)

    records = repository.replace_for_user(
        user.id,
        ["Programming", "Music", "Travel"],
    )
    db.commit()

    assert len(records) == 3

    interests = repository.get_by_user_id(user.id)
    assert {item.interest for item in interests} == {
        "Programming", "Music", "Travel"
    }


def test_interests_are_scoped_to_the_user(db):
    user = create_user(db)
    other_user = create_user(db)
    repository = UserInterestRepository(db)

    repository.replace_for_user(user.id, ["Programming"])
    repository.replace_for_user(other_user.id, ["Cooking"])
    db.commit()

    assert {
        item.interest
        for item in repository.get_by_user_id(user.id)
    } == {"Programming"}

    assert {
        item.interest
        for item in repository.get_by_user_id(other_user.id)
    } == {"Cooking"}


def test_replace_removes_previous_interests(db):
    user = create_user(db)
    repository = UserInterestRepository(db)

    repository.replace_for_user(
        user.id,
        ["Programming", "Music"],
    )
    db.commit()

    repository.replace_for_user(
        user.id,
        ["Photography"],
    )
    db.commit()

    assert {
        item.interest
        for item in repository.get_by_user_id(user.id)
    } == {"Photography"}


def test_replace_with_empty_list_clears_interests(db):
    user = create_user(db)
    repository = UserInterestRepository(db)

    repository.replace_for_user(
        user.id,
        ["Programming", "Music"],
    )
    db.commit()

    repository.replace_for_user(user.id, [])
    db.commit()

    assert repository.get_by_user_id(user.id) == []