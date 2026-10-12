from datetime import datetime, timedelta, timezone

import pytest

from app.exceptions.invitation_exceptions import (
    InvitationCodeAlreadyUsedException,
    InvitationCodeExpiredException,
    InvitationCodeNotFoundException,
)
from app.models.invitation_code import InvitationCode
from app.repositories.invitation_code_repository import (
    InvitationCodeRepository,
)
from app.services.invitation_code_service import InvitationCodeService


def create_invitation(
    db,
    code: str,
    configuration_key: str = "default",
    used: bool = False,
    expires_at=None,
):
    invitation = InvitationCode(
        code=code,
        configuration_key=configuration_key,
        used=used,
        expires_at=expires_at,
    )

    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    return invitation


def test_claim_valid_invitation(db):
    create_invitation(
        db,
        code="TEST123",
        configuration_key="default",
    )

    repository = InvitationCodeRepository(db)
    service = InvitationCodeService(repository)

    result = service.claim("TEST123")

    assert result == "default"

    invitation = repository.get_by_code("TEST123")
    assert invitation is not None
    assert invitation.used is True


def test_claim_invalid_invitation(db):
    repository = InvitationCodeRepository(db)
    service = InvitationCodeService(repository)

    with pytest.raises(InvitationCodeNotFoundException):
        service.claim("INVALID")


def test_claim_used_invitation(db):
    create_invitation(
        db,
        code="USED123",
        used=True,
    )

    repository = InvitationCodeRepository(db)
    service = InvitationCodeService(repository)

    with pytest.raises(InvitationCodeAlreadyUsedException):
        service.claim("USED123")


def test_claim_expired_invitation(db):
    expired_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    create_invitation(
        db,
        code="EXPIRED123",
        expires_at=expired_at,
    )

    repository = InvitationCodeRepository(db)
    service = InvitationCodeService(repository)

    with pytest.raises(InvitationCodeExpiredException):
        service.claim("EXPIRED123")


def test_claim_rejects_code_claimed_after_initial_validation(db, monkeypatch):
    create_invitation(
        db,
        code="RACE123",
        configuration_key="default",
    )

    repository = InvitationCodeRepository(db)
    service = InvitationCodeService(repository)

    def simulate_concurrent_claim(code: str) -> None:
        return None

    monkeypatch.setattr(
        repository,
        "claim_if_unused",
        simulate_concurrent_claim,
    )

    with pytest.raises(InvitationCodeAlreadyUsedException):
        service.claim("RACE123")