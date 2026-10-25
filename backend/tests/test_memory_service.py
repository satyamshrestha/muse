from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.friend_group import FriendGroup
from app.models.group_membership import GroupMembership
from app.models.memory import Memory
from app.models.user import User
from app.services.memory_service import MemoryService


def create_user(db: Session) -> User:
    user = User(
        email=f"{uuid4().hex}@example.com",
        password_hash="test-hash",
        display_name="Memory Service Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_group(db: Session, owner: User) -> FriendGroup:
    group = FriendGroup(name=f"Memory Group {uuid4().hex[:8]}")
    db.add(group)
    db.flush()

    membership = GroupMembership(
        group_id=group.id,
        user_id=owner.id,
    )
    db.add(membership)
    db.commit()
    db.refresh(group)
    return group


def add_member(db: Session, group: FriendGroup, user: User) -> None:
    db.add(
        GroupMembership(
            group_id=group.id,
            user_id=user.id,
        )
    )
    db.commit()


def test_create_memory_for_group_member(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    service = MemoryService(db)

    memory = service.create_memory(
        group.id,
        user.id,
        "Summer trip",
        "Our group trip.",
    )

    assert memory.id is not None
    assert memory.group_id == group.id
    assert memory.created_by == user.id
    assert memory.title == "Summer trip"
    assert memory.description == "Our group trip."


def test_create_memory_rejects_non_member(db: Session):
    owner = create_user(db)
    outsider = create_user(db)
    group = create_group(db, owner)
    service = MemoryService(db)

    with pytest.raises(ValueError, match="not a member"):
        service.create_memory(group.id, outsider.id, "Unauthorized")


def test_create_memory_rejects_missing_group(db: Session):
    user = create_user(db)
    service = MemoryService(db)

    with pytest.raises(ValueError, match="Group not found"):
        service.create_memory(uuid4(), user.id, "Missing group")


def test_get_memory_for_group_member(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    service = MemoryService(db)
    memory = service.create_memory(group.id, user.id, "Birthday")

    result = service.get_memory(group.id, memory.id, user.id)

    assert result.id == memory.id


def test_get_memory_rejects_non_member(db: Session):
    owner = create_user(db)
    outsider = create_user(db)
    group = create_group(db, owner)
    memory = MemoryService(db).create_memory(
        group.id, owner.id, "Birthday"
    )

    with pytest.raises(ValueError, match="not a member"):
        MemoryService(db).get_memory(group.id, memory.id, outsider.id)


def test_get_memory_rejects_wrong_group(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    other_group = create_group(db, user)
    service = MemoryService(db)
    memory = service.create_memory(group.id, user.id, "Birthday")

    with pytest.raises(ValueError, match="Memory not found"):
        service.get_memory(other_group.id, memory.id, user.id)


def test_list_memories_only_returns_group_memories(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    other_group = create_group(db, user)
    service = MemoryService(db)

    service.create_memory(group.id, user.id, "Trip")
    service.create_memory(group.id, user.id, "Birthday")
    service.create_memory(other_group.id, user.id, "Other group")

    memories = service.list_memories(group.id, user.id)

    assert len(memories) == 2
    assert all(memory.group_id == group.id for memory in memories)


@pytest.mark.parametrize("limit", [0, 101])
def test_list_memories_rejects_invalid_limit(db: Session, limit: int):
    user = create_user(db)
    group = create_group(db, user)
    service = MemoryService(db)

    with pytest.raises(ValueError, match="Limit must be between 1 and 100"):
        service.list_memories(group.id, user.id, limit=limit)


def test_list_memories_rejects_negative_offset(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    service = MemoryService(db)

    with pytest.raises(ValueError, match="Offset cannot be negative"):
        service.list_memories(group.id, user.id, offset=-1)


def test_update_memory_by_creator(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    service = MemoryService(db)
    memory = service.create_memory(
        group.id, user.id, "Old title", "Old description"
    )

    updated = service.update_memory(
        group.id,
        memory.id,
        user.id,
        title="New title",
        description="New description",
    )

    assert updated.title == "New title"
    assert updated.description == "New description"


def test_update_memory_rejects_non_creator(db: Session):
    owner = create_user(db)
    member = create_user(db)
    group = create_group(db, owner)
    add_member(db, group, member)
    service = MemoryService(db)
    memory = service.create_memory(group.id, owner.id, "Birthday")

    with pytest.raises(ValueError, match="Only the memory creator"):
        service.update_memory(
            group.id,
            memory.id,
            member.id,
            title="Changed",
            description=None,
        )


def test_update_memory_rejects_missing_memory(db: Session):
    user = create_user(db)
    group = create_group(db, user)

    with pytest.raises(ValueError, match="Memory not found"):
        MemoryService(db).update_memory(
            group.id,
            uuid4(),
            user.id,
            title="Missing",
            description=None,
        )


def test_delete_memory_by_creator(db: Session):
    user = create_user(db)
    group = create_group(db, user)
    service = MemoryService(db)
    memory = service.create_memory(group.id, user.id, "Temporary")

    assert service.delete_memory(group.id, memory.id, user.id) is True
    assert service.memory_repository.get_by_id_for_group(
        memory.id, group.id
    ) is None


def test_delete_memory_rejects_non_creator(db: Session):
    owner = create_user(db)
    member = create_user(db)
    group = create_group(db, owner)
    add_member(db, group, member)
    service = MemoryService(db)
    memory = service.create_memory(group.id, owner.id, "Birthday")

    with pytest.raises(ValueError, match="Only the memory creator"):
        service.delete_memory(group.id, memory.id, member.id)


def test_delete_memory_rejects_missing_memory(db: Session):
    user = create_user(db)
    group = create_group(db, user)

    with pytest.raises(ValueError, match="Memory not found"):
        MemoryService(db).delete_memory(group.id, uuid4(), user.id)