from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.base_configuration import BaseConfiguration
from app.models.user import User
from app.repositories.user_repository import UserRepository


def create_user(db: Session) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_configuration(db: Session) -> BaseConfiguration:
    configuration = BaseConfiguration(
        name=f"config-{uuid4().hex[:8]}",
        interests=["technology"],
        preferences={"theme": "dark"},
    )
    db.add(configuration)
    db.commit()
    db.refresh(configuration)
    return configuration


def test_get_by_email_returns_matching_user(db: Session):
    user = create_user(db)
    repository = UserRepository(db)

    result = repository.get_by_email(user.email)

    assert result is not None
    assert result.id == user.id


def test_get_by_email_returns_none_for_unknown_email(db: Session):
    repository = UserRepository(db)

    assert repository.get_by_email("missing@example.com") is None


def test_get_by_id_returns_matching_user(db: Session):
    user = create_user(db)
    repository = UserRepository(db)

    result = repository.get_by_id(user.id)

    assert result is not None
    assert result.email == user.email


def test_get_by_id_returns_none_for_unknown_id(db: Session):
    repository = UserRepository(db)

    assert repository.get_by_id(uuid4()) is None


def test_create_user(db: Session):
    repository = UserRepository(db)

    user = repository.create(
        email="created@example.com",
        password_hash="secure-hash",
        display_name="Created User",
    )
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert user.email == "created@example.com"
    assert user.password_hash == "secure-hash"
    assert user.display_name == "Created User"
    assert user.bio is None
    assert user.created_at is not None

    assert repository.get_by_id(user.id) is not None


def test_update_profile_changes_display_name(db: Session):
    user = create_user(db)
    repository = UserRepository(db)

    updated = repository.update_profile(
        user.id,
        display_name="Updated User",
    )

    assert updated is not None
    assert updated.display_name == "Updated User"
    assert updated.bio is None


def test_update_profile_changes_bio(db: Session):
    user = create_user(db)
    repository = UserRepository(db)

    updated = repository.update_profile(
        user.id,
        bio="A short bio.",
    )

    assert updated is not None
    assert updated.display_name == "Test User"
    assert updated.bio == "A short bio."


def test_update_profile_can_set_empty_bio(db: Session):
    user = create_user(db)
    repository = UserRepository(db)

    repository.update_profile(user.id, bio="Existing bio")

    updated = repository.update_profile(user.id, bio="")

    assert updated is not None
    assert updated.bio == ""


def test_update_profile_returns_none_for_missing_user(db: Session):
    repository = UserRepository(db)

    assert repository.update_profile(
        uuid4(),
        display_name="Missing",
    ) is None


def test_update_password(db: Session):
    user = create_user(db)
    repository = UserRepository(db)

    updated = repository.update_password(
        user.id,
        password_hash="new-secure-hash",
    )

    assert updated is not None
    assert updated.password_hash == "new-secure-hash"


def test_update_password_returns_none_for_missing_user(db: Session):
    repository = UserRepository(db)

    assert repository.update_password(
        uuid4(),
        password_hash="new-hash",
    ) is None


def test_attach_base_configuration(db: Session):
    user = create_user(db)
    configuration = create_configuration(db)
    repository = UserRepository(db)

    updated = repository.attach_base_configuration(
        user.id,
        configuration.id,
    )

    assert updated is not None
    assert updated.base_configuration_id == configuration.id


def test_attach_base_configuration_returns_none_for_missing_user(
    db: Session,
):
    repository = UserRepository(db)

    assert repository.attach_base_configuration(
        uuid4(),
        uuid4(),
    ) is None