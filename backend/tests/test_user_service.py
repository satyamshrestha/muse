from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.exceptions.user_exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from app.services.user_service import UserService


@pytest.fixture
def repository():
    repo = Mock()
    repo.db = Mock()

    # Default behavior: no existing user is found.
    repo.get_by_email.return_value = None
    repo.get_by_id.return_value = None
    repo.update_profile.return_value = None
    repo.update_password.return_value = None

    return repo


@pytest.fixture
def service(repository):
    return UserService(repository)


def test_create_user_hashes_password_and_commits(
    service, repository, monkeypatch
):
    user = SimpleNamespace(id=uuid4())
    repository.create.return_value = user

    hash_mock = Mock(return_value="hashed-password")
    monkeypatch.setattr(
        "app.services.user_service.hash_password",
        hash_mock,
    )

    result = service.create_user(
        email="user@example.com",
        password="Password123!",
        display_name="Test User",
    )

    assert result is user
    hash_mock.assert_called_once_with("Password123!")
    repository.get_by_email.assert_called_once_with(
        "user@example.com"
    )
    repository.create.assert_called_once_with(
        email="user@example.com",
        password_hash="hashed-password",
        display_name="Test User",
    )
    repository.db.commit.assert_called_once()


def test_create_user_rejects_duplicate_email(
    service, repository, monkeypatch
):
    repository.get_by_email.return_value = SimpleNamespace(
        email="user@example.com"
    )
    hash_mock = Mock()
    monkeypatch.setattr(
        "app.services.user_service.hash_password",
        hash_mock,
    )

    with pytest.raises(UserAlreadyExistsException):
        service.create_user(
            email="user@example.com",
            password="Password123!",
            display_name="Test User",
        )

    repository.create.assert_not_called()
    repository.db.commit.assert_not_called()
    hash_mock.assert_not_called()


def test_login_returns_user_with_valid_credentials(
    service, repository, monkeypatch
):
    user = SimpleNamespace(password_hash="stored-hash")
    repository.get_by_email.return_value = user

    verify_mock = Mock(return_value=True)
    monkeypatch.setattr(
        "app.services.user_service.verify_password",
        verify_mock,
    )

    result = service.login("user@example.com", "Password123!")

    assert result is user
    verify_mock.assert_called_once_with(
        "Password123!",
        "stored-hash",
    )


@pytest.mark.parametrize(
    "user",
    [
        None,
        SimpleNamespace(password_hash="stored-hash"),
    ],
)
def test_login_rejects_missing_user_or_invalid_password(
    service, repository, monkeypatch, user
):
    repository.get_by_email.return_value = user

    verify_mock = Mock(return_value=False)
    monkeypatch.setattr(
        "app.services.user_service.verify_password",
        verify_mock,
    )

    with pytest.raises(InvalidCredentialsException):
        service.login("user@example.com", "WrongPassword!")

    if user is None:
        verify_mock.assert_not_called()
    else:
        verify_mock.assert_called_once_with(
            "WrongPassword!",
            "stored-hash",
        )


def test_get_by_email_delegates_to_repository(
    service, repository
):
    user = SimpleNamespace(email="user@example.com")
    repository.get_by_email.return_value = user

    result = service.get_by_email("user@example.com")

    assert result is user
    repository.get_by_email.assert_called_once_with(
        "user@example.com"
    )


def test_get_by_id_delegates_to_repository(
    service, repository
):
    user_id = uuid4()
    user = SimpleNamespace(id=user_id)
    repository.get_by_id.return_value = user

    result = service.get_by_id(user_id)

    assert result is user
    repository.get_by_id.assert_called_once_with(user_id)


def test_update_profile_returns_updated_user(
    service, repository
):
    user_id = uuid4()
    user = SimpleNamespace(id=user_id)
    repository.update_profile.return_value = user

    result = service.update_profile(
        user_id=user_id,
        display_name="Updated User",
        bio="Updated bio",
    )

    assert result is user
    repository.update_profile.assert_called_once_with(
        user_id=user_id,
        display_name="Updated User",
        bio="Updated bio",
    )


def test_update_profile_raises_when_user_is_missing(
    service, repository
):
    with pytest.raises(UserNotFoundException):
        service.update_profile(
            user_id=uuid4(),
            display_name="Updated User",
        )


def test_change_password_updates_password_hash(
    service, repository, monkeypatch
):
    user_id = uuid4()
    user = SimpleNamespace(password_hash="old-hash")
    repository.get_by_id.return_value = user

    verify_mock = Mock(return_value=True)
    hash_mock = Mock(return_value="new-hash")

    monkeypatch.setattr(
        "app.services.user_service.verify_password",
        verify_mock,
    )
    monkeypatch.setattr(
        "app.services.user_service.hash_password",
        hash_mock,
    )

    service.change_password(
        user_id=user_id,
        current_password="OldPassword123!",
        new_password="NewPassword123!",
    )

    verify_mock.assert_called_once_with(
        "OldPassword123!",
        "old-hash",
    )
    hash_mock.assert_called_once_with("NewPassword123!")
    repository.update_password.assert_called_once_with(
        user_id=user_id,
        password_hash="new-hash",
    )


def test_change_password_rejects_missing_user(
    service, repository, monkeypatch
):
    hash_mock = Mock()

    monkeypatch.setattr(
        "app.services.user_service.hash_password",
        hash_mock,
    )

    with pytest.raises(UserNotFoundException):
        service.change_password(
            user_id=uuid4(),
            current_password="OldPassword123!",
            new_password="NewPassword123!",
        )

    repository.update_password.assert_not_called()
    hash_mock.assert_not_called()


def test_change_password_rejects_wrong_current_password(
    service, repository, monkeypatch
):
    repository.get_by_id.return_value = SimpleNamespace(
        password_hash="old-hash"
    )

    monkeypatch.setattr(
        "app.services.user_service.verify_password",
        Mock(return_value=False),
    )
    hash_mock = Mock()
    monkeypatch.setattr(
        "app.services.user_service.hash_password",
        hash_mock,
    )

    with pytest.raises(InvalidCredentialsException):
        service.change_password(
            user_id=uuid4(),
            current_password="WrongPassword!",
            new_password="NewPassword123!",
        )

    repository.update_password.assert_not_called()
    hash_mock.assert_not_called()