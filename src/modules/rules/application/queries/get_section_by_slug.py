"""Get section by ID query."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TypedDict
from uuid import UUID

from modules.rules.domain.entities.section import Section
from modules.rules.domain.exceptions import SectionNotFoundError
from modules.rules.domain.ports import SectionRepositoryPort

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class GetSectionBySlugRequest:
    """Request to get a section by slug."""

    slug: str


class SectionDetailResponse(TypedDict):
    """Detailed section response data."""

    id: UUID
    name: str
    slug: str
    description: str
    status: str
    created_at: datetime
    updated_at: datetime


class GetSectionBySlugQuery:
    """Query to get a section by its slug."""

    def __init__(self, section_repository: SectionRepositoryPort) -> None:
        self._section_repository = section_repository

    async def execute(self, request: GetSectionBySlugRequest) -> SectionDetailResponse:
        """
        Execute the get section by slug query.

        :param request: The request with section slug
        :return: Detailed section response
        :raises SectionNotFoundError: When section is not found
        """
        log.info("Fetching section by slug: %s", request.slug)

        # Fetch section from repository
        section: Section | None = await self._section_repository.find_one_by_slug(
            request.slug
        )

        if section is None:
            log.warning("Section not found: %s", request.slug)
            raise SectionNotFoundError(str(request.slug))

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
