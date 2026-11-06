from uuid import uuid4

import pytest

from app.exceptions.base_configuration_exceptions import (
    BaseConfigurationNotFoundException,
)
from app.models.base_configuration import BaseConfiguration
from app.models.user import User
from app.repositories.base_configuration_repository import (
    BaseConfigurationRepository,
)
from app.services.base_configuration_service import (
    BaseConfigurationService,
)


def clear_configurations(db):
    db.query(User).update(
        {User.base_configuration_id: None},
        synchronize_session=False,
    )
    db.query(BaseConfiguration).delete(
        synchronize_session=False
    )
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


def test_list_configurations_returns_all_configurations(db):
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
    service = BaseConfigurationService(repository)

    result = service.list_configurations()

    result_ids = {item.id for item in result}

    assert first.id in result_ids
    assert second.id in result_ids


def test_list_configurations_returns_empty_list(db):
    clear_configurations(db)

    repository = BaseConfigurationRepository(db)
    service = BaseConfigurationService(repository)

    result = service.list_configurations()

    assert result == []


def test_get_configuration_returns_configuration(db):
    clear_configurations(db)

    configuration = create_configuration(
        db,
        name=f"Configuration {uuid4()}",
        interests=["coding", "AI"],
        preferences={"theme": "dark"},
    )

    repository = BaseConfigurationRepository(db)
    service = BaseConfigurationService(repository)

    result = service.get_configuration(configuration.id)

    assert result.id == configuration.id
    assert result.name == configuration.name
    assert result.interests == ["coding", "AI"]
    assert result.preferences == {"theme": "dark"}


def test_get_configuration_raises_when_not_found(db):
    clear_configurations(db)

    repository = BaseConfigurationRepository(db)
    service = BaseConfigurationService(repository)

    with pytest.raises(BaseConfigurationNotFoundException):
        service.get_configuration(uuid4())