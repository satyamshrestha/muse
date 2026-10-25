from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.friend_group import FriendGroup
from app.models.memory import Memory
from app.models.user import User
from app.repositories.memory_repository import MemoryRepository


def create_user(db: Session) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Memory Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_group(db: Session) -> FriendGroup:
    group = FriendGroup(name=f"Memories {uuid4().hex[:8]}")
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def test_create_memory(db: Session):
    user = create_user(db)
    group = create_group(db)
    repository = MemoryRepository(db)

    memory = repository.create(
        group_id=group.id,
        created_by=user.id,
        title="Summer trip",
        description="Our group trip.",
    )
    db.commit()
    db.refresh(memory)

    assert memory.id is not None
    assert memory.group_id == group.id
    assert memory.created_by == user.id
    assert memory.title == "Summer trip"
    assert memory.description == "Our group trip."
    assert memory.memory_date is None
    assert memory.created_at is not None


def test_create_memory_with_memory_date(db: Session):
    from datetime import datetime, timezone

    user = create_user(db)
    group = create_group(db)
    repository = MemoryRepository(db)
    memory_date = datetime(2026, 7, 10, tzinfo=timezone.utc)

    memory = repository.create(
        group.id,
        user.id,
        "Summer trip",
        "Our group trip.",
        memory_date,
    )
    db.commit()
    db.refresh(memory)

    assert memory.memory_date == memory_date


def test_get_by_id_for_group_returns_matching_memory(db: Session):
    user = create_user(db)
    group = create_group(db)
    repository = MemoryRepository(db)

    memory = repository.create(group.id, user.id, "Birthday")
    db.commit()

    result = repository.get_by_id_for_group(memory.id, group.id)

    assert result is not None
    assert result.id == memory.id


def test_get_by_id_for_group_hides_memory_from_another_group(
    db: Session,
):
    user = create_user(db)
    group = create_group(db)
    another_group = create_group(db)
    repository = MemoryRepository(db)

    memory = repository.create(group.id, user.id, "Birthday")
    db.commit()

    assert (
        repository.get_by_id_for_group(memory.id, another_group.id)
        is None
    )


def test_get_by_id_for_group_returns_none_for_unknown_id(
    db: Session,
):
    group = create_group(db)
    repository = MemoryRepository(db)

    assert repository.get_by_id_for_group(uuid4(), group.id) is None


def test_list_by_group_only_returns_memories_for_that_group(
    db: Session,
):
    user = create_user(db)
    group = create_group(db)
    another_group = create_group(db)
    repository = MemoryRepository(db)

    repository.create(group.id, user.id, "Trip")
    repository.create(group.id, user.id, "Birthday")
    repository.create(another_group.id, user.id, "Other group")
    db.commit()

    memories = repository.list_by_group(group.id)

    assert len(memories) == 2
    assert {memory.title for memory in memories} == {
        "Trip",
        "Birthday",
    }
    assert all(memory.group_id == group.id for memory in memories)


def test_list_by_group_returns_empty_list_when_no_memories(
    db: Session,
):
    group = create_group(db)
    repository = MemoryRepository(db)

    assert repository.list_by_group(group.id) == []


def test_list_by_group_supports_pagination(db: Session):
    user = create_user(db)
    group = create_group(db)
    repository = MemoryRepository(db)

    for number in range(3):
        repository.create(group.id, user.id, f"Memory {number}")
    db.commit()

    first_page = repository.list_by_group(
        group.id, limit=2, offset=0
    )
    second_page = repository.list_by_group(
        group.id, limit=2, offset=2
    )

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert {item.id for item in first_page}.isdisjoint(
        {item.id for item in second_page}
    )


def test_update_memory(db: Session):
    user = create_user(db)
    group = create_group(db)
    repository = MemoryRepository(db)

    memory = repository.create(
        group.id, user.id, "Old title", "Old description"
    )
    db.commit()

    updated = repository.update(
        memory,
        title="New title",
        description="New description",
    )
    db.commit()
    db.refresh(updated)

    assert updated.title == "New title"
    assert updated.description == "New description"
    assert updated.memory_date is None


def test_update_memory_can_clear_optional_fields(db: Session):
    user = create_user(db)
    group = create_group(db)
    repository = MemoryRepository(db)

    memory = repository.create(
        group.id, user.id, "Trip", "Trip description"
    )
    db.commit()

    repository.update(
        memory,
        title="Trip",
        description=None,
        memory_date=None,
    )
    db.commit()
    db.refresh(memory)

    assert memory.description is None
    assert memory.memory_date is None


def test_delete_memory(db: Session):
    user = create_user(db)
    group = create_group(db)
    repository = MemoryRepository(db)

    memory = repository.create(group.id, user.id, "Temporary")
    db.commit()
    memory_id = memory.id

    repository.delete(memory)
    db.commit()

    assert repository.get_by_id_for_group(memory_id, group.id) is None