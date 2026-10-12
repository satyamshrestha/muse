from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.services.personalization_service import PersonalizationService


def build_service(
    *,
    user=None,
    configuration=None,
    configuration_key="default",
):
    db = Mock()
    user_repository = Mock()
    user_repository.db = db
    user_repository.get_by_id.return_value = user

    invitation_service = Mock()
    invitation_service.claim.return_value = configuration_key

    configuration_repository = Mock()
    configuration_repository.get_by_name.return_value = configuration

    service = PersonalizationService(
        user_repository=user_repository,
        invitation_service=invitation_service,
        configuration_repository=configuration_repository,
        user_interest_repository=Mock(),
        user_preference_repository=Mock(),
        feature_preference_repository=Mock(),
        notification_preference_repository=Mock(),
    )

    return service, db, user_repository, invitation_service


def test_claim_configuration_commits_after_assignment():
    user = SimpleNamespace(
        id=uuid4(),
        base_configuration_id=None,
    )
    configuration = SimpleNamespace(
        id=uuid4(),
        name="default",
    )

    service, db, _, invitation_service = build_service(
        user=user,
        configuration=configuration,
    )

    result = service.claim_configuration(
        user_id=user.id,
        code="TEST123",
    )

    assert result is configuration
    assert user.base_configuration_id == configuration.id
    invitation_service.claim.assert_called_once_with("TEST123")
    db.commit.assert_called_once()
    db.rollback.assert_not_called()
    db.refresh.assert_called_once_with(user)


def test_claim_configuration_rolls_back_when_configuration_is_missing():
    user = SimpleNamespace(
        id=uuid4(),
        base_configuration_id=None,
    )

    service, db, _, invitation_service = build_service(
        user=user,
        configuration=None,
        configuration_key="missing-configuration",
    )

    with pytest.raises(
        ValueError,
        match="Base configuration not found",
    ):
        service.claim_configuration(
            user_id=user.id,
            code="TEST123",
        )

    assert user.base_configuration_id is None
    invitation_service.claim.assert_called_once_with("TEST123")
    db.commit.assert_not_called()
    db.rollback.assert_called_once()


def test_claim_configuration_rolls_back_when_user_is_missing():
    service, db, _, invitation_service = build_service(
        user=None,
        configuration=None,
    )

    from app.exceptions.user_exceptions import UserNotFoundException

    with pytest.raises(UserNotFoundException):
        service.claim_configuration(
            user_id=uuid4(),
            code="TEST123",
        )

    invitation_service.claim.assert_not_called()
    db.commit.assert_not_called()
    db.rollback.assert_called_once()