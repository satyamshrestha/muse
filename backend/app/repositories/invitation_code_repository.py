from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.invitation_code import InvitationCode


class InvitationCodeRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, code: str) -> InvitationCode | None:
        return self.db.scalar(
            select(InvitationCode).where(
                InvitationCode.code == code
            )
        )

    def consume(self, invitation: InvitationCode) -> None:
        invitation.used = True
        self.db.commit()

    def claim_if_unused(self, code: str) -> str | None:
        statement = (
            update(InvitationCode)
            .where(
                InvitationCode.code == code,
                InvitationCode.used.is_(False),
            )
            .values(used=True)
            .returning(InvitationCode.configuration_key)
        )

        return self.db.scalar(statement)