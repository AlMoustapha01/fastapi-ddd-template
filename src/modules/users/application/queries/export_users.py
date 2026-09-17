"""Export users query."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TypedDict

from core.lib.db.repository.paginated import (
    FilterBy,
    FilterGroup,
    Operator,
    PaginatedQueryParams,
)
from modules.auth.infrastructure.keycloak import KeycloakClient
from modules.users.domain.ports import UserRepositoryPort
from modules.users.domain.user import User

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ExportUsersRequest:
    """Request to export users."""

    group_id: str | None = None
    is_active: bool | None = None
    search: str | None = None


class ExportUserData(TypedDict):
    """User data for export."""

    id: str
    name: str
    email: str
    username: str
    keycloak_id: str
    is_active: str
    created_at: str
    updated_at: str
    groups: str
    last_login: str
    connected: str


class ExportUsersQuery:
    """Query to export all users."""

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        keycloak_client: KeycloakClient,
    ) -> None:
        self._user_repository = user_repository
        self._keycloak_client = keycloak_client

    async def execute(self, request: ExportUsersRequest) -> list[ExportUserData]:  # noqa: C901
        """
        Execute the export users query.

        :param request: The export request with filters
        :return: List of users for export
        """
        log.info(
            "Exporting users: group_id=%s, is_active=%s, search=%s",
            request.group_id,
            request.is_active,
            request.search,
        )

        # Build filters
        filters: list[FilterBy[User]] = []
        filter_groups: list[FilterGroup[User]] = []

        if request.is_active is not None:
            filters.append(
                FilterBy[User](
                    field="is_active",
                    operator=Operator.EQ,
                    value=request.is_active,
                )
            )

        # Search across name, email, and username with OR logic
        if request.search:
            search_filters = [
                FilterBy[User](
                    field="name",
                    operator=Operator.ILIKE,
                    value=f"%{request.search}%",
                ),
                FilterBy[User](
                    field="email",
                    operator=Operator.ILIKE,
                    value=f"%{request.search}%",
                ),
                FilterBy[User](
                    field="username",
                    operator=Operator.ILIKE,
                    value=f"%{request.search}%",
                ),
            ]
            filter_groups.append(FilterGroup[User](filters=search_filters, use_or=True))

        # Fetch all users with large limit (for export)
        params = PaginatedQueryParams[User](
            page=1,
            limit=10000,  # Large limit for export
            filter_by=filters if filters else None,
            filter_groups=filter_groups if filter_groups else None,
        )

        paginated = await self._user_repository.find_all_paginated(params)
        filtered_users = list(paginated.data)

        # Map to export data with Keycloak info
        users_data: list[ExportUserData] = []
        for user in filtered_users:
            # Get groups from Keycloak
            try:
                keycloak_groups = await self._keycloak_client.get_user_groups(
                    user.props.keycloak_id
                )
                # Filter by group_id if specified
                if request.group_id:
                    group_ids = [group.id for group in keycloak_groups]
                    if request.group_id not in group_ids:
                        continue

                groups_str = ", ".join([group.name for group in keycloak_groups])
            except Exception:
                log.exception("Failed to get user groups")
                groups_str = ""
                # Skip user if group filter is active and we can't get groups
                if request.group_id:
                    continue

            # Get last login from login events
            last_login_str = ""
            try:
                login_events = await self._keycloak_client.get_user_login_events(
                    user_id=user.props.keycloak_id,
                    event_types=["LOGIN"],
                    max_results=1,
                )
                if login_events:
                    last_login = datetime.fromtimestamp(
                        login_events[0].time / 1000, tz=UTC
                    )
                    last_login_str = last_login.isoformat()
            except Exception:
                log.exception("Failed to get user login events")

            # Check if user is currently connected
            connected_str = "No"
            try:
                active_sessions = await self._keycloak_client.get_user_active_sessions(
                    user.props.keycloak_id
                )
                connected_str = "Yes" if len(active_sessions) > 0 else "No"
            except Exception:
                log.exception("Failed to get user active sessions")

            users_data.append(
                ExportUserData(
                    id=str(user.id_.value),
                    name=user.props.name,
                    email=user.props.email.value,
                    username=user.props.username,
                    keycloak_id=user.props.keycloak_id,
                    is_active="Active" if user.props.is_active else "Inactive",
                    created_at=user.created_at_.isoformat(),
                    updated_at=user.updated_at_.isoformat(),
                    groups=groups_str,
                    last_login=last_login_str if last_login_str else "Never",
                    connected=connected_str,
                )
            )

        log.info("Exported %d users", len(users_data))
        return users_data
