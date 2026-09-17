"""Bulk create sections command."""

import logging
from dataclasses import dataclass
from typing import TypedDict
from uuid import UUID

from core.lib.db.transaction_manager import TransactionManager
from modules.rules.application.commands.create_section_flusher_sqla import (
    SqlaSectionFlusher,
)
from modules.rules.domain.entities.section import CreateSectionProps, Section
from modules.rules.domain.ports import SectionRepositoryPort
from modules.rules.domain.value_objects import SlugValueObject

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class BulkCreateSectionItem:
    """Single section item for bulk creation."""

    name: str
    description: str


@dataclass(frozen=True, slots=True, kw_only=True)
class BulkCreateSectionsRequest:
    """Request to create multiple sections."""

    sections: list[BulkCreateSectionItem]
    created_by_user_id: UUID


class BulkCreateSectionResult(TypedDict):
    """Result for a single section creation."""

    id: UUID
    name: str
    slug: str


class BulkCreateSectionsResponse(TypedDict):
    """Response for bulk section creation."""

    created: list[BulkCreateSectionResult]
    skipped: list[str]
    total_created: int
    total_skipped: int


class BulkCreateSectionsCommand:
    """Command to create multiple sections at once."""

    def __init__(
        self,
        section_repository: SectionRepositoryPort,
        section_flusher: SqlaSectionFlusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._section_repository = section_repository
        self._flusher = section_flusher
        self._transaction_manager = transaction_manager

    async def execute(
        self, request: BulkCreateSectionsRequest
    ) -> BulkCreateSectionsResponse:
        """
        Execute the bulk create sections command.

        Skips sections that already exist (based on slug).

        :param request: The bulk section creation request
        :return: Response with created and skipped sections
        """
        log.info("Creating %d sections in bulk", len(request.sections))

        created_sections: list[Section] = []
        skipped_slugs: list[str] = []

        for section_item in request.sections:
            # Generate slug to check if section already exists
            slug = SlugValueObject.from_text(section_item.name)
            existing = await self._section_repository.find_one_by_slug(slug.value)

            if existing:
                log.debug("Skipping existing section with slug: %s", slug.value)
                skipped_slugs.append(slug.value)
                continue

            section = Section.create(
                props=CreateSectionProps(
                    name=section_item.name,
                    description=section_item.description,
                    created_by_user_id=request.created_by_user_id,
                )
            )
            await self._section_repository.add(section)
            created_sections.append(section)

        if created_sections:
            await self._flusher.flush()
            await self._transaction_manager.commit()

        log.info(
            "Bulk create completed: %d created, %d skipped",
            len(created_sections),
            len(skipped_slugs),
        )

        return BulkCreateSectionsResponse(
            created=[
                BulkCreateSectionResult(
                    id=section.id_.value,
                    name=section.props.name,
                    slug=section.props.slug.value,
                )
                for section in created_sections
            ],
            skipped=skipped_slugs,
            total_created=len(created_sections),
            total_skipped=len(skipped_slugs),
        )
