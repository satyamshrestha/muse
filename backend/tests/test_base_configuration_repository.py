from uuid import uuid4

from sqlalchemy import update

from app.models.base_configuration import BaseConfiguration
from app.models.user import User
from app.repositories.base_configuration_repository import (
    BaseConfigurationRepository,
)


def clear_configurations(db):
    db.execute(
        update(User).values(base_configuration_id=None)
    )
    db.query(BaseConfiguration).delete()
    db.commit()


def create_configuration(
    db,
    name: str,
    interests: list[str] | None = None,
    preferences: dict | None = None,
) -> BaseConfiguration:
    configuration = BaseConfiguration(
        name=name,
        interests=interests or [],
        preferences=preferences or {},
    )

    db.add(configuration)
    db.commit()
    db.refresh(configuration)

    return configuration


def test_list_all_returns_configurations(db):
    clear_configurations(db)

    first = create_configuration(
        db,
        name=f"Configuration A {uuid4()}",
        interests=["coding"],
        preferences={"theme": "dark"},
    )
    second = create_configuration(
        db,
        name=f"Configuration B {uuid4()}",
        interests=["gaming"],
        preferences={"theme": "light"},
    )

    repository = BaseConfigurationRepository(db)

    result = repository.list_all()

    result_ids = {item.id for item in result}

    assert first.id in result_ids
    assert second.id in result_ids


def test_list_all_returns_empty_list_when_no_configurations(db):
    clear_configurations(db)

    repository = BaseConfigurationRepository(db)

    result = repository.list_all()

    assert result == []


def test_list_all_orders_configurations_by_name(db):
    clear_configurations(db)

    create_configuration(db, name="Zulu")
    create_configuration(db, name="Alpha")
    create_configuration(db, name="Mike")

    repository = BaseConfigurationRepository(db)

    result = repository.list_all()

    names = [item.name for item in result]

    assert names == ["Alpha", "Mike", "Zulu"]


def test_list_all_uses_id_as_secondary_order(db):
    clear_configurations(db)

    first = BaseConfiguration(
        name="Shared",
        interests=[],
        preferences={},
    )
    second = BaseConfiguration(
        name="Shared",
        interests=[],
        preferences={},
    )

    db.add_all([first, second])
    db.commit()
    db.refresh(first)
    db.refresh(second)

    repository = BaseConfigurationRepository(db)

    result = repository.list_all()

    ids = [item.id for item in result]

    assert ids == sorted(ids)