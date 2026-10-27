from datetime import datetime, timezone
from uuid import uuid4

from app.models.friend_group import FriendGroup
from app.models.plan import Plan
from app.models.user import User
from app.repositories.plan_repository import PlanRepository


def create_test_user(db) -> User:
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed-password",
        display_name="Plan Tester",
    )
    db.add(user)
    db.flush()
    return user


def create_test_group(db) -> FriendGroup:
    group = FriendGroup(name="Plan Crew")
    db.add(group)
    db.flush()
    return group


def test_plan_repository_create(db):
    user = create_test_user(db)
    group = create_test_group(db)
    repository = PlanRepository(db)

    plan = repository.create(
        group_id=group.id,
        created_by=user.id,
        title="Weekend trip",
        description="Plan our weekend.",
    )
    db.commit()

    saved = db.query(Plan).filter(Plan.id == plan.id).first()

    assert saved is not None
    assert saved.group_id == group.id
    assert saved.created_by == user.id
    assert saved.title == "Weekend trip"
    assert saved.description == "Plan our weekend."
    assert saved.starts_at is None
    assert saved.ends_at is None


def test_plan_repository_get_by_id(db):
    user = create_test_user(db)
    group = create_test_group(db)
    repository = PlanRepository(db)

    plan = repository.create(
        group_id=group.id,
        created_by=user.id,
        title="Game night",
    )

    result = repository.get_by_id(plan.id)

    assert result is not None
    assert result.id == plan.id
    assert result.title == "Game night"


def test_plan_repository_get_by_id_not_found(db):
    repository = PlanRepository(db)

    assert repository.get_by_id(uuid4()) is None


def test_plan_repository_list_by_group(db):
    user = create_test_user(db)
    group = create_test_group(db)
    other_group = FriendGroup(name="Other Crew")
    db.add(other_group)
    db.flush()

    repository = PlanRepository(db)

    first = repository.create(
        group_id=group.id,
        created_by=user.id,
        title="First plan",
    )
    second = repository.create(
        group_id=group.id,
        created_by=user.id,
        title="Second plan",
    )
    other = repository.create(
        group_id=other_group.id,
        created_by=user.id,
        title="Other group plan",
    )
    db.commit()

    plans = repository.list_by_group(group.id)

    assert {plan.id for plan in plans} == {first.id, second.id}
    assert other.id not in {plan.id for plan in plans}


def test_plan_repository_list_by_group_supports_pagination(db):
    user = create_test_user(db)
    group = create_test_group(db)
    repository = PlanRepository(db)

    for index in range(3):
        repository.create(
            group_id=group.id,
            created_by=user.id,
            title=f"Plan {index}",
        )
    db.commit()

    first_page = repository.list_by_group(
        group.id,
        limit=2,
        offset=0,
    )
    second_page = repository.list_by_group(
        group.id,
        limit=2,
        offset=2,
    )

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert first_page[0].id != second_page[0].id


def test_plan_repository_update(db):
    user = create_test_user(db)
    group = create_test_group(db)
    repository = PlanRepository(db)

    plan = repository.create(
        group_id=group.id,
        created_by=user.id,
        title="Old title",
        description="Old description",
    )
    starts_at = datetime(2026, 11, 1, tzinfo=timezone.utc)
    ends_at = datetime(2026, 11, 2, tzinfo=timezone.utc)

    updated = repository.update(
        plan,
        title="Updated title",
        description="Updated description",
        starts_at=starts_at,
        ends_at=ends_at,
    )
    db.commit()

    assert updated.title == "Updated title"
    assert updated.description == "Updated description"
    assert updated.starts_at == starts_at
    assert updated.ends_at == ends_at


def test_plan_repository_delete(db):
    user = create_test_user(db)
    group = create_test_group(db)
    repository = PlanRepository(db)

    plan = repository.create(
        group_id=group.id,
        created_by=user.id,
        title="Temporary plan",
    )
    db.commit()
    plan_id = plan.id

    repository.delete(plan)
    db.commit()

    assert repository.get_by_id(plan_id) is None