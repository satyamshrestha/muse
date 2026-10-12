from datetime import datetime, timezone

from app.exceptions.invitation_exceptions import (
    InvitationCodeAlreadyUsedException,
    InvitationCodeExpiredException,
    InvitationCodeNotFoundException,
)
from app.repositories.invitation_code_repository import (
    InvitationCodeRepository,
)


class InvitationCodeService:
    def __init__(self, repository: InvitationCodeRepository):
        self.repository = repository

    def claim(self, code: str) -> str:
        invitation = self.repository.get_by_code(code)

        if invitation is None:
            raise InvitationCodeNotFoundException()

        if invitation.used:
            raise InvitationCodeAlreadyUsedException()

        if (
            invitation.expires_at is not None
            and invitation.expires_at <= datetime.now(timezone.utc)
        ):
            raise InvitationCodeExpiredException()

        configuration_key = self.repository.claim_if_unused(code)

        if configuration_key is None:
            raise InvitationCodeAlreadyUsedException()

        return configuration_key