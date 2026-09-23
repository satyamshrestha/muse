import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate


def test_user_create_accepts_valid_data():
    user = UserCreate(
        email="test@example.com",
        password="password123",
        display_name="Test User",
    )

    assert user.email == "test@example.com"
    assert user.password == "password123"
    assert user.display_name == "Test User"


def test_user_create_rejects_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(
            email="not-an-email",
            password="password123",
            display_name="Test User",
        )


def test_user_create_requires_password():
    with pytest.raises(ValidationError):
        UserCreate(
            email="test@example.com",
            display_name="Test User",
        )