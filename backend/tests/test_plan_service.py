from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.models.friend_group import FriendGroup
from app.models.plan import Plan
from app.models.user import User
from app.repositories.group_membership_repository import (
    GroupMembershipRepository,
)
from app.services.plan_service import PlanService


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
    group = FriendGroup(name=f"Plan Crew {uuid4()}")
    db.add(group)
    db.flush()
    return group


def add_member(db, user: User, group: FriendGroup) -> None:
    GroupMembershipRepository(db).create(
        user_id=user.id,
        group_id=group.id,
    )


def create_plan_context(db):
    user = create_test_user(db)
    group = create_test_group(db)
    add_member(db, user, group)
    db.commit()
    return user, group, PlanService(db)


def test_plan_service_create_plan(db):
    user, group, service = create_plan_context(db)
    starts_at = datetime(2026, 11, 1, tzinfo=timezone.utc)
    ends_at = datetime(2026, 11, 2, tzinfo=timezone.utc)

    plan = service.create_plan(
        group_id=group.id,
        user_id=user.id,
        title="Weekend trip",
        description="Plan our weekend.",
        starts_at=starts_at,
        ends_at=ends_at,
    )

    assert plan.id is not None
    assert plan.group_id == group.id
    assert plan.created_by == user.id
    assert plan.title == "Weekend trip"
    assert plan.description == "Plan our weekend."
    assert plan.starts_at == starts_at
    assert plan.ends_at == ends_at


def test_plan_service_create_plan_rejects_non_member(db):
    user = create_test_user(db)
    group = create_test_group(db)
    db.commit()
    service = PlanService(db)

    with pytest.raises(
        ValueError,
        match="User is not a member of this group",
    ):
        service.create_plan(
            group_id=group.id,
            user_id=user.id,
            title="Unauthorized plan",
        )


def test_plan_service_create_plan_rejects_missing_group(db):
    user = create_test_user(db)
    db.commit()
    service = PlanService(db)

    with pytest.raises(ValueError, match="Group not found"):
        service.create_plan(
            group_id=uuid4(),
            user_id=user.id,
            title="Missing group plan",
        )


def test_plan_service_create_plan_rejects_invalid_schedule(db):
    user, group, service = create_plan_context(db)

    with pytest.raises(
        ValueError,
        match="Plan end time cannot be before its start time",
    ):
        service.create_plan(
            group_id=group.id,
            user_id=user.id,
            title="Invalid schedule",
            starts_at=datetime(2026, 11, 2, tzinfo=timezone.utc),
            ends_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
        )


def test_plan_service_get_plan(db):
    user, group, service = create_plan_context(db)
    plan = service.create_plan(
        group_id=group.id,
        user_id=user.id,
        title="Game night",
    )

    result = service.get_plan(
        group_id=group.id,
        plan_id=plan.id,
        user_id=user.id,
    )

    assert result.id == plan.id
    assert result.title == "Game night"


def test_plan_service_get_plan_rejects_missing_plan(db):
    user, group, service = create_plan_context(db)

    with pytest.raises(ValueError, match="Plan not found"):
        service.get_plan(
            group_id=group.id,
            plan_id=uuid4(),
            user_id=user.id,
        )


def test_plan_service_get_plan_rejects_plan_from_another_group(db):
    user, group, service = create_plan_context(db)
    other_group = create_test_group(db)
    add_member(db, user, other_group)
    db.commit()

    plan = service.create_plan(
        group_id=other_group.id,
        user_id=user.id,
        title="Other group plan",
    )

    with pytest.raises(ValueError, match="Plan not found"):
        service.get_plan(
            group_id=group.id,
            plan_id=plan.id,
            user_id=user.id,
        )


def test_plan_service_list_plans_only_returns_group_plans(db):
    user, group, service = create_plan_context(db)
    other_group = create_test_group(db)
    add_member(db, user, other_group)
    db.commit()

    first = service.create_plan(
        group_id=group.id,
        user_id=user.id,
        title="First plan",
    )
    second = service.create_plan(
        group_id=group.id,
        user_id=user.id,
        title="Second plan",
    )
    other = service.create_plan(
        group_id=other_group.id,
        user_id=user.id,
        title="Other group plan",
    )

    plans = service.list_plans(group.id, user.id)

    assert {plan.id for plan in plans} == {first.id, second.id}
    assert other.id not in {plan.id for plan in plans}


def test_plan_service_list_plans_supports_pagination(db):
    user, group, service = create_plan_context(db)

    for index in range(3):
        service.create_plan(
            group_id=group.id,
            user_id=user.id,
            title=f"Plan {index}",
        )

    first_page = service.list_plans(
        group.id,
        user.id,
        limit=2,
        offset=0,
    )
    second_page = service.list_plans(
        group.id,
        user.id,
        limit=2,
        offset=2,
    )

    assert len(first_page) == 2
    assert len(second_page) == 1
    assert first_page[0].id != second_page[0].id


@pytest.mark.parametrize("limit", [0, -1, 101])
def test_plan_service_list_plans_rejects_invalid_limit(db, limit):
    user, group, service = create_plan_context(db)

    with pytest.raises(
        ValueError,
        match="Limit must be between 1 and 100",
    ):
        service.list_plans(
            group_id=group.id,
            user_id=user.id,
            limit=limit,
        )


def test_plan_service_list_plans_rejects_negative_offset(db):
    user, group, service = create_plan_context(db)

    with pytest.raises(
        ValueError,
        match="Offset cannot be negative",
    ):
        service.list_plans(
            group_id=group.id,
            user_id=user.id,
            offset=-1,
        )


def test_plan_service_update_plan(db):
    user, group, service = create_plan_context(db)
    plan = service.create_plan(
        group_id=group.id,
        user_id=user.id,
        title="Old title",
        description="Old description",
    )
    starts_at = datetime(2026, 11, 1, tzinfo=timezone.utc)
    ends_at = datetime(2026, 11, 2, tzinfo=timezone.utc)

    updated = service.update_plan(
        group_id=group.id,
        plan_id=plan.id,
        user_id=user.id,
        title="Updated title",
        description="Updated description",
        starts_at=starts_at,
        ends_at=ends_at,
    )

    assert updated.title == "Updated title"
    assert updated.description == "Updated description"
    assert updated.starts_at == starts_at
    assert updated.ends_at == ends_at


def test_plan_service_update_plan_rejects_non_creator(db):
    creator, group, service = create_plan_context(db)
    plan = service.create_plan(
        group_id=group.id,
        user_id=creator.id,
        title="Creator's plan",
    )

    other_user = create_test_user(db)
    add_member(db, other_user, group)
    db.commit()

    with pytest.raises(
        ValueError,
        match="Only the plan creator can update it",
    ):
        service.update_plan(
            group_id=group.id,
            plan_id=plan.id,
            user_id=other_user.id,
            title="Unauthorized update",
            description=None,
        )


def test_plan_service_update_plan_rejects_invalid_schedule(db):
    user, group, service = create_plan_context(db)
    plan = service.create_plan(
        group_id=group.id,
        user_id=user.id,
        title="Scheduled plan",
    )

    with pytest.raises(
        ValueError,
        match="Plan end time cannot be before its start time",
    ):
        service.update_plan(
            group_id=group.id,
            plan_id=plan.id,
            user_id=user.id,
            title="Invalid schedule",
            description=None,
            starts_at=datetime(2026, 11, 2, tzinfo=timezone.utc),
            ends_at=datetime(2026, 11, 1, tzinfo=timezone.utc),
        )


def test_plan_service_delete_plan(db):
    user, group, service = create_plan_context(db)
    plan = service.create_plan(
        group_id=group.id,
        user_id=user.id,
        title="Temporary plan",
    )
    plan_id = plan.id

    assert service.delete_plan(
        group_id=group.id,
        plan_id=plan_id,
        user_id=user.id,
    ) is True

    assert db.query(Plan).filter(Plan.id == plan_id).first() is None


def test_plan_service_delete_plan_rejects_non_creator(db):
    creator, group, service = create_plan_context(db)
    plan = service.create_plan(
        group_id=group.id,
        user_id=creator.id,
        title="Creator's plan",
    )

    other_user = create_test_user(db)
    add_member(db, other_user, group)
    db.commit()

    with pytest.raises(
        ValueError,
        match="Only the plan creator can delete it",
    ):
        service.delete_plan(
            group_id=group.id,
            plan_id=plan.id,
            user_id=other_user.id,
        )