from uuid import uuid4

from app.models.friend_group import FriendGroup
from app.models.plan import Plan
from app.models.plan_participant import PlanParticipant
from app.models.user import User
from app.repositories.plan_participant_repository import (
    PlanParticipantRepository,
)


def create_test_user(db) -> User:
    user = User(
        email=f"{uuid4()}@example.com",
        password_hash="hashed-password",
        display_name="Participant Tester",
    )
    db.add(user)
    db.flush()
    return user


def create_test_group(db) -> FriendGroup:
    group = FriendGroup(name="Plan Crew")
    db.add(group)
    db.flush()
    return group


def create_test_plan(db, creator: User, group: FriendGroup) -> Plan:
    plan = Plan(
        group_id=group.id,
        created_by=creator.id,
        title="Weekend Trip",
    )
    db.add(plan)
    db.flush()
    return plan


def test_plan_participant_repository_create(db):
    creator = create_test_user(db)
    participant_user = create_test_user(db)
    group = create_test_group(db)
    plan = create_test_plan(db, creator, group)

    repository = PlanParticipantRepository(db)

    participant = repository.create(
        plan_id=plan.id,
        user_id=participant_user.id,
    )
    db.commit()

    saved = db.query(PlanParticipant).filter(
        PlanParticipant.id == participant.id
    ).first()

    assert saved is not None
    assert saved.plan_id == plan.id
    assert saved.user_id == participant_user.id
    assert saved.status == "invited"


def test_plan_participant_repository_get_by_id(db):
    creator = create_test_user(db)
    participant_user = create_test_user(db)
    group = create_test_group(db)
    plan = create_test_plan(db, creator, group)

    repository = PlanParticipantRepository(db)
    participant = repository.create(
        plan.id,
        participant_user.id,
    )

    result = repository.get_by_id(participant.id)

    assert result is not None
    assert result.id == participant.id


def test_plan_participant_repository_get_by_id_not_found(db):
    repository = PlanParticipantRepository(db)

    assert repository.get_by_id(uuid4()) is None


def test_get_for_plan_returns_only_plan_participants(db):
    creator = create_test_user(db)
    first_user = create_test_user(db)
    second_user = create_test_user(db)
    other_user = create_test_user(db)

    group = create_test_group(db)
    other_group = FriendGroup(name="Other Crew")
    db.add(other_group)
    db.flush()

    first_plan = create_test_plan(db, creator, group)
    second_plan = Plan(
        group_id=other_group.id,
        created_by=creator.id,
        title="Other Plan",
    )
    db.add(second_plan)
    db.flush()

    repository = PlanParticipantRepository(db)

    first = repository.create(first_plan.id, first_user.id)
    second = repository.create(first_plan.id, second_user.id)
    other = repository.create(second_plan.id, other_user.id)
    db.commit()

    participants = repository.get_for_plan(first_plan.id)

    assert {p.id for p in participants} == {
        first.id,
        second.id,
    }
    assert other.id not in {p.id for p in participants}


def test_get_for_user_and_plan_returns_matching_participant(db):
    creator = create_test_user(db)
    participant_user = create_test_user(db)
    group = create_test_group(db)
    plan = create_test_plan(db, creator, group)

    repository = PlanParticipantRepository(db)
    participant = repository.create(
        plan.id,
        participant_user.id,
    )

    result = repository.get_for_user_and_plan(
        participant_user.id,
        plan.id,
    )

    assert result is not None
    assert result.id == participant.id


def test_get_for_user_and_plan_returns_none_when_missing(db):
    creator = create_test_user(db)
    participant_user = create_test_user(db)
    group = create_test_group(db)
    plan = create_test_plan(db, creator, group)

    repository = PlanParticipantRepository(db)

    assert (
        repository.get_for_user_and_plan(
            participant_user.id,
            plan.id,
        )
        is None
    )


def test_update_status(db):
    creator = create_test_user(db)
    participant_user = create_test_user(db)
    group = create_test_group(db)
    plan = create_test_plan(db, creator, group)

    repository = PlanParticipantRepository(db)
    participant = repository.create(
        plan.id,
        participant_user.id,
    )

    updated = repository.update_status(
        participant,
        status="accepted",
    )
    db.commit()

    assert updated.status == "accepted"


def test_delete_participant(db):
    creator = create_test_user(db)
    participant_user = create_test_user(db)
    group = create_test_group(db)
    plan = create_test_plan(db, creator, group)

    repository = PlanParticipantRepository(db)
    participant = repository.create(
        plan.id,
        participant_user.id,
    )
    db.commit()

    deleted = repository.delete(participant.id)
    db.commit()

    assert deleted is True
    assert repository.get_by_id(participant.id) is None