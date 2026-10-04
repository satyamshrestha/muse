from sqlalchemy import select
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