from app.models.invitation_code import InvitationCode
from app.repositories.invitation_code_repository import (
    InvitationCodeRepository,
)


def create_invitation(
    db,
    code: str,
    configuration_key: str = "default",
    used: bool = False,
) -> InvitationCode:
    invitation = InvitationCode(
        code=code,
        configuration_key=configuration_key,
        used=used,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def test_claim_if_unused_marks_code_used_and_returns_configuration(db):
    create_invitation(
        db,
        code="ATOMIC-001",
        configuration_key="starter",
    )

    repository = InvitationCodeRepository(db)

    result = repository.claim_if_unused("ATOMIC-001")

    assert result == "starter"

    invitation = repository.get_by_code("ATOMIC-001")
    assert invitation is not None
    assert invitation.used is True


def test_claim_if_unused_rejects_already_used_code(db):
    create_invitation(
        db,
        code="ATOMIC-002",
        used=True,
    )

    repository = InvitationCodeRepository(db)

    result = repository.claim_if_unused("ATOMIC-002")

    assert result is None


def test_claim_if_unused_rejects_unknown_code(db):
    repository = InvitationCodeRepository(db)

    result = repository.claim_if_unused("DOES-NOT-EXIST")

    assert result is None


def test_claim_if_unused_only_claims_code_once(db):
    create_invitation(
        db,
        code="ATOMIC-003",
        configuration_key="focus",
    )

    repository = InvitationCodeRepository(db)

    first_result = repository.claim_if_unused("ATOMIC-003")
    second_result = repository.claim_if_unused("ATOMIC-003")

    assert first_result == "focus"
    assert second_result is None