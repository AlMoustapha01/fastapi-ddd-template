"""Get section by ID query."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from uuid import UUID

from modules.rules.domain.entities.section import Section
from modules.rules.domain.exceptions import SectionNotFoundError
from modules.rules.domain.ports import SectionRepositoryPort
from modules.rules.domain.value_objects import SectionId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetSectionByIdRequest:
    """Request to get a section by ID."""

    id: UUID


class SectionDetailResponse(TypedDict):
    """Detailed section response data."""

    id: UUID
    name: str
    slug: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime


class GetSectionByIdQuery:
    """Query to get a section by its ID."""

    def __init__(self, section_repository: SectionRepositoryPort) -> None:
        self._section_repository = section_repository

    async def execute(self, request: GetSectionByIdRequest) -> SectionDetailResponse:
        """
        Execute the get section by ID query.

        :param request: The request with section ID
        :return: Detailed section response
        :raises SectionNotFoundError: When section is not found
        """
        log.info("Fetching section by ID: %s", request.id)

        # Create SectionId value object
        section_id = SectionId(request.id)

        # Fetch section from repository
        section: Section | None = await self._section_repository.find_one_by_id(
            section_id
        )

        if section is None:
            log.warning("Section not found: %s", request.id)
            raise SectionNotFoundError(str(request.id))

        log.info("Section found: %s", section.id_.value)

        # Map to response
        return SectionDetailResponse(
            id=section.id_.value,
            name=section.props.name,
            slug=section.props.slug.value,
            description=section.props.description,
            status=section.props.status.value,
            created_at=section.created_at_,
            updated_at=section.updated_at_,
        )
