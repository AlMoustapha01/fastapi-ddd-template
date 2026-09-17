"""Get users query."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TypedDict
from uuid import UUID

from core.lib.db.repository.paginated import (
    FilterBy,
    FilterGroup,
    Operator,
    OrderBy,
    Paginated,
    PaginatedQueryParams,
    SortOrder,
)
from core.services import GroupData
from modules.auth.infrastructure.keycloak import KeycloakClient
from modules.users.domain.ports import UserRepositoryPort
from modules.users.domain.user import User

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetUsersRequest:
    """Request to get users with pagination."""

    page: int = 1
    limit: int = 10
    order_by_field: str | None = None
    order_by_direction: SortOrder = SortOrder.ASC
    group_id: str | None = None
    is_active: bool | None = None
    search: str | None = None


class UserResponse(TypedDict):
    """User response data."""

    id: UUID
    name: str
    email: str
    username: str
    keycloak_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    groups: list[GroupData]
    last_login: datetime | None
    connected: bool


class GetUsersResponse(TypedDict):
    """Paginated users response."""

    count: int
    limit: int
    page: int
    total_pages: int
    has_next: bool
    has_previous: bool
    data: list[UserResponse]


class GetUsersQuery:
    """Query to get all users with pagination."""

    def __init__(
        self,
        user_repository: UserRepositoryPort,
        keycloak_client: KeycloakClient,
    ) -> None:
        self._user_repository = user_repository
        self._keycloak_client = keycloak_client

    async def execute(self, request: GetUsersRequest) -> GetUsersResponse:  # noqa: C901
        """
        Execute the get users query.

        :param request: The pagination request
        :return: Paginated users response
        """
        log.info(
            "Fetching users: page=%d, limit=%d, group_id=%s, is_active=%s, search=%s",
            request.page,
            request.limit,
            request.group_id,
            request.is_active,
            request.search,
        )

        # Build query params
        order_by = None
        if request.order_by_field:
            order_by = OrderBy[User](
                field=request.order_by_field,
                param=request.order_by_direction,
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

        params = PaginatedQueryParams[User](
            page=request.page,
            limit=request.limit,
            order_by=order_by,
            filter_by=filters if filters else None,
            filter_groups=filter_groups if filter_groups else None,
        )

        # Fetch paginated users
        paginated: Paginated[User] = await self._user_repository.find_all_paginated(
            params
        )

        log.info(
            "Fetched %d users (page %d/%d)",
            len(paginated.data),
            paginated.page,
            paginated.total_pages,
        )

        # Map to response with Keycloak data
        users_data: list[UserResponse] = []
        for user in paginated.data:
            # Get groups from Keycloak
            try:
                keycloak_groups = await self._keycloak_client.get_user_groups(
                    user.props.keycloak_id
                )
                groups = [
                    GroupData(
                        id=group.id,
                        name=group.name,
                        path=group.path,
                    )
                    for group in keycloak_groups
                ]

                # Filter by group_id if specified
                if request.group_id:
                    group_ids = [group.id for group in keycloak_groups]
                    if request.group_id not in group_ids:
                        continue
            except Exception:
                groups = []
                # Skip user if group filter is active and we can't get groups
                if request.group_id:
                    continue

            # Get last login from login events
            last_login = None
            try:
                login_events = await self._keycloak_client.get_user_login_events(
                    user_id=user.props.keycloak_id,
                    event_types=["LOGIN"],
                    max_results=1,
                )
                if login_events:
                    # Convert timestamp (milliseconds) to datetime
                    last_login = datetime.fromtimestamp(
                        login_events[0].time / 1000, tz=UTC
                    )
            except Exception:
                log.exception("Failed to get user login events")
                pass

            # Check if user is currently connected
            connected = False
            try:
                active_sessions = await self._keycloak_client.get_user_active_sessions(
                    user.props.keycloak_id
                )
                connected = len(active_sessions) > 0
            except Exception:
                log.exception("Failed to get user active sessions")
                pass

            users_data.append(
                UserResponse(
                    id=user.id_.value,
                    name=user.props.name,
                    email=user.props.email.value,
                    username=user.props.username,
                    keycloak_id=user.props.keycloak_id,
                    is_active=user.props.is_active,
                    created_at=user.created_at_,
                    updated_at=user.updated_at_,
                    groups=groups,
                    last_login=last_login,
                    connected=connected,
                )
            )

        return GetUsersResponse(
            count=paginated.count,
            limit=paginated.limit,
            page=paginated.page,
            total_pages=paginated.total_pages,
            has_next=paginated.has_next,
            has_previous=paginated.has_previous,
            data=users_data,
        )
