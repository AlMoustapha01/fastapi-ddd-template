"""Group management controllers."""

from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from modules.auth.application.commands import (
    MoveUserToGroupCommand,
    handle_move_user_to_group,
)
from modules.auth.application.dependencies import require_roles
from modules.auth.application.queries import (
    ListGroupRolesQuery,
    ListGroupsQuery,
    handle_list_group_roles,
    handle_list_groups,
)
from modules.auth.domain import AuthUser
from modules.auth.infrastructure.keycloak import KeycloakClient


class GroupResponse(BaseModel):
    """Group response."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    path: str


class RoleResponse(BaseModel):
    """Role response."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    description: str | None
    composite: bool


class MoveUserToGroupRequest(BaseModel):
    """Move user to group request."""

    model_config = ConfigDict(frozen=True)

    user_id: str
    old_group_id: str
    new_group_id: str


def create_groups_router() -> APIRouter:
    """Create groups router."""
    router = APIRouter()

    @router.get(
        "/groups",
        response_model=list[GroupResponse],
        summary="List groups",
        description="List all groups (requires perm_view_group role)",
    )
    @inject
    async def list_groups(
        keycloak_client: FromDishka[KeycloakClient],
        _: Annotated[AuthUser, Depends(require_roles(["perm_view_group"]))],
    ) -> list[GroupResponse]:
        """List groups endpoint."""
        query = ListGroupsQuery()
        groups = await handle_list_groups(query, keycloak_client)

        return [
            GroupResponse(id=group.id, name=group.name, path=group.path)
            for group in groups
        ]

    @router.get(
        "/groups/{group_id}/roles",
        response_model=list[RoleResponse],
        summary="List group roles",
        description="List roles for a group (requires perm_view_group role)",
    )
    @inject
    async def list_group_roles(
        group_id: str,
        keycloak_client: FromDishka[KeycloakClient],
        _: Annotated[AuthUser, Depends(require_roles(["perm_view_group"]))],
    ) -> list[RoleResponse]:
        """List group roles endpoint."""
        query = ListGroupRolesQuery(group_id=group_id)
        roles = await handle_list_group_roles(query, keycloak_client)

        return [
            RoleResponse(
                id=role.id,
                name=role.name,
                description=role.description,
                composite=role.composite,
            )
            for role in roles
        ]

    @router.patch(
        "/groups/users/move",
        summary="Move user to group",
        description="Move user from current group to new group \
            (requires perm_user_group role). \
            The user will be removed from the old group and added to the new group.",
        status_code=204,
    )
    @inject
    async def move_user_to_group(
        request: MoveUserToGroupRequest,
        keycloak_client: FromDishka[KeycloakClient],
        _: Annotated[AuthUser, Depends(require_roles(["perm_user_group"]))],
    ) -> None:
        """Move user to group endpoint."""
        command = MoveUserToGroupCommand(
            user_id=request.user_id,
            old_group_id=request.old_group_id,
            new_group_id=request.new_group_id,
        )
        await handle_move_user_to_group(command, keycloak_client)

    return router
