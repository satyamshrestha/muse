from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.memory import Memory


class MemoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        group_id: UUID,
        created_by: UUID,
        title: str,
        description: str | None = None,
        memory_date=None,
    ) -> Memory:
        memory = Memory(
            group_id=group_id,
            created_by=created_by,
            title=title,
            description=description,
            memory_date=memory_date,
        )
        self.db.add(memory)
        self.db.flush()
        return memory

    def get_by_id_for_group(
        self,
        memory_id: UUID,
        group_id: UUID,
    ) -> Memory | None:
        statement = select(Memory).where(
            Memory.id == memory_id,
            Memory.group_id == group_id,
        )
        return self.db.scalar(statement)

    def list_by_group(
        self,
        group_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Memory]:
        statement = (
            select(Memory)
            .where(Memory.group_id == group_id)
            .order_by(
                Memory.created_at.desc(),
                Memory.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(statement).all())

    def update(
        self,
        memory: Memory,
        *,
        title: str,
        description: str | None,
        memory_date=None,
    ) -> Memory:
        memory.title = title
        memory.description = description
        memory.memory_date = memory_date
        self.db.flush()
        return memory

    def delete(self, memory: Memory) -> None:
        self.db.delete(memory)
        self.db.flush()