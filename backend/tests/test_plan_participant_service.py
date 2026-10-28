from uuid import uuid4

import pytest

from app.models.friend_group import FriendGroup
from app.models.plan import Plan
from app.models.plan_participant import PlanParticipant
from app.models.user import User
from app.repositories.group_membership_repository import (
    GroupMembershipRepository,
)
from app.services.plan_participant_service import (
    PlanParticipantService,
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
    creator = create_test_user(db)
    group = create_test_group(db)
    add_member(db, creator, group)

    plan = Plan(
        group_id=group.id,
        created_by=creator.id,
        title="Weekend Trip",
    )
    db.add(plan)
    db.commit()

    return creator, group, plan, PlanParticipantService(db)


def test_invite_participant(db):
    creator, group, plan, service = create_plan_context(db)
    invitee = create_test_user(db)
    add_member(db, invitee, group)
    db.commit()

    participant = service.invite_participant(
        plan_id=plan.id,
        requester_id=creator.id,
        participant_user_id=invitee.id,
    )

    assert participant.plan_id == plan.id
    assert participant.user_id == invitee.id
    assert participant.status == "invited"


def test_invite_rejects_non_creator(db):
    creator, group, plan, service = create_plan_context(db)
    member = create_test_user(db)
    invitee = create_test_user(db)
    add_member(db, member, group)
    add_member(db, invitee, group)
    db.commit()

    with pytest.raises(
        ValueError,
        match="Only the plan creator can invite participants",
    ):
        service.invite_participant(
            plan.id,
            member.id,
            invitee.id,
        )


def test_invite_rejects_non_member_target(db):
    creator, group, plan, service = create_plan_context(db)
    outsider = create_test_user(db)
    db.commit()

    with pytest.raises(
        ValueError,
        match="User is not a member of this group",
    ):
        service.invite_participant(
            plan.id,
            creator.id,
            outsider.id,
        )


def test_invite_rejects_duplicate_participant(db):
    creator, group, plan, service = create_plan_context(db)
    invitee = create_test_user(db)
    add_member(db, invitee, group)
    db.commit()

    service.invite_participant(plan.id, creator.id, invitee.id)

    with pytest.raises(
        ValueError,
        match="User has already been invited to this plan",
    ):
        service.invite_participant(
            plan.id,
            creator.id,
            invitee.id,
        )


def test_invite_rejects_missing_plan(db):
    creator, _, _, service = create_plan_context(db)
    invitee = create_test_user(db)
    db.commit()

    with pytest.raises(ValueError, match="Plan not found"):
        service.invite_participant(
            uuid4(),
            creator.id,
            invitee.id,
        )


def test_list_participants_only_returns_plan_participants(db):
    creator, group, plan, service = create_plan_context(db)
    first_user = create_test_user(db)
    second_user = create_test_user(db)
    add_member(db, first_user, group)
    add_member(db, second_user, group)

    other_plan = Plan(
        group_id=group.id,
        created_by=creator.id,
        title="Another Plan",
    )
    db.add(other_plan)
    db.commit()

    first = service.invite_participant(
        plan.id, creator.id, first_user.id
    )
    second = service.invite_participant(
        plan.id, creator.id, second_user.id
    )
    other = service.invite_participant(
        other_plan.id, creator.id, second_user.id
    )

    participants = service.list_participants(plan.id, creator.id)

    assert {p.id for p in participants} == {first.id, second.id}
    assert other.id not in {p.id for p in participants}


def test_list_participants_rejects_non_member(db):
    _, _, plan, service = create_plan_context(db)
    outsider = create_test_user(db)
    db.commit()

    with pytest.raises(
        ValueError,
        match="User is not a member of this group",
    ):
        service.list_participants(plan.id, outsider.id)


def test_participant_can_accept_invitation(db):
    creator, group, plan, service = create_plan_context(db)
    invitee = create_test_user(db)
    add_member(db, invitee, group)
    db.commit()

    service.invite_participant(plan.id, creator.id, invitee.id)

    updated = service.respond_to_invitation(
        plan.id,
        invitee.id,
        "accepted",
    )

    assert updated.status == "accepted"


def test_participant_can_decline_invitation(db):
    creator, group, plan, service = create_plan_context(db)
    invitee = create_test_user(db)
    add_member(db, invitee, group)
    db.commit()

    service.invite_participant(plan.id, creator.id, invitee.id)

    updated = service.respond_to_invitation(
        plan.id,
        invitee.id,
        "declined",
    )

    assert updated.status == "declined"


def test_response_rejects_invalid_status(db):
    creator, group, plan, service = create_plan_context(db)
    invitee = create_test_user(db)
    add_member(db, invitee, group)
    db.commit()

    service.invite_participant(plan.id, creator.id, invitee.id)

    with pytest.raises(
        ValueError,
        match="Status must be either",
    ):
        service.respond_to_invitation(
            plan.id,
            invitee.id,
            "maybe",
        )


def test_response_rejects_user_without_invitation(db):
    creator, group, plan, service = create_plan_context(db)
    member = create_test_user(db)
    add_member(db, member, group)
    db.commit()

    with pytest.raises(
        ValueError,
        match="Plan participant not found",
    ):
        service.respond_to_invitation(
            plan.id,
            member.id,
            "accepted",
        )


def test_creator_can_remove_participant(db):
    creator, group, plan, service = create_plan_context(db)
    invitee = create_test_user(db)
    add_member(db, invitee, group)
    db.commit()

    participant = service.invite_participant(
        plan.id,
        creator.id,
        invitee.id,
    )

    deleted = service.remove_participant(
        plan.id,
        creator.id,
        invitee.id,
    )

    assert deleted is True
    assert (
        service.participant_repository.get_by_id(participant.id)
        is None
    )


def test_non_creator_cannot_remove_participant(db):
    creator, group, plan, service = create_plan_context(db)
    member = create_test_user(db)
    invitee = create_test_user(db)
    add_member(db, member, group)
    add_member(db, invitee, group)
    db.commit()

    service.invite_participant(plan.id, creator.id, invitee.id)

    with pytest.raises(
        ValueError,
        match="Only the plan creator can remove participants",
    ):
        service.remove_participant(
            plan.id,
            member.id,
            invitee.id,
        )


def test_remove_rejects_missing_participant(db):
    creator, _, plan, service = create_plan_context(db)

    with pytest.raises(
        ValueError,
        match="Plan participant not found",
    ):
        service.remove_participant(
            plan.id,
            creator.id,
            uuid4(),
        )


def test_remove_rejects_missing_plan(db):
    creator, _, _, service = create_plan_context(db)

    with pytest.raises(ValueError, match="Plan not found"):
        service.remove_participant(
            uuid4(),
            creator.id,
            uuid4(),
        )


def test_participant_cannot_respond_after_leaving_group(db):
    creator, group, plan, service = create_plan_context(db)
    invitee = create_test_user(db)
    add_member(db, invitee, group)
    db.commit()

    service.invite_participant(plan.id, creator.id, invitee.id)

    GroupMembershipRepository(db).delete_membership(
        user_id=invitee.id,
        group_id=group.id,
    )
    db.commit()

    with pytest.raises(
        ValueError,
        match="User is not a member of this group",
    ):
        service.respond_to_invitation(
            plan.id,
            invitee.id,
            "accepted",
        )