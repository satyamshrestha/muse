from uuid import UUID

from fastapi import APIRouter, Depends

from app.auth.jwt import get_current_user_id
from app.schemas.base_configuration_schema import (
    BaseConfigurationResponse,
)
from app.services.base_configuration_service import (
    BaseConfigurationService,
)
from app.services.dependencies import (
    get_base_configuration_service,
)


router = APIRouter(
    prefix="/base-configurations",
    tags=["Base Configurations"],
)


@router.get(
    "",
    response_model=list[BaseConfigurationResponse],
)
def list_base_configurations(
    user_id: UUID = Depends(get_current_user_id),
    service: BaseConfigurationService = Depends(
        get_base_configuration_service
    ),
):
    return service.list_configurations()


@router.get(
    "/{configuration_id}",
    response_model=BaseConfigurationResponse,
)
def get_base_configuration(
    configuration_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    service: BaseConfigurationService = Depends(
        get_base_configuration_service
    ),
):
    return service.get_configuration(configuration_id)