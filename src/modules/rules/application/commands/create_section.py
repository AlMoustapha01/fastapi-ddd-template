"""Create section command."""

import logging
from dataclasses import dataclass
from typing import TypedDict
from uuid import UUID

from core.lib.db.flusher import Flusher
from core.lib.db.transaction_manager import TransactionManager
from modules.rules.domain.entities.section import CreateSectionProps, Section
from modules.rules.domain.exceptions import SectionAlreadyExistsError
from modules.rules.domain.ports import SectionRepositoryPort

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateSectionRequest:
    name: str
    description: str
    created_by_user_id: UUID


class CreateSectionResponse(TypedDict):
    id: UUID


class CreateSectionCommand:
    """Command to create a new section."""

    def __init__(
        self,
        section_repository: SectionRepositoryPort,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._section_repository = section_repository
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: CreateSectionRequest) -> CreateSectionResponse:
        """
        Execute the create section command.

        :param request: The section creation request
        :return: Response with the created section ID
        :raises SectionAlreadyExistsError: When a section with the same slug exists
        """
        log.info("Creating section: %s", request.name)

        # Create domain entity
        section = Section.create(
            props=CreateSectionProps(
                name=request.name,
                description=request.description,
                created_by_user_id=request.created_by_user_id,
            )
        )

        # Add to repository (no commit yet)
        await self._section_repository.add(section)

        # Flush to database (validates constraints)
        try:
            await self._flusher.flush()
        except SectionAlreadyExistsError:
            log.warning(
                "Section already exists with slug: %s", section.props.slug.value
            )
            raise

        # Commit transaction
        await self._transaction_manager.commit()

        log.info("Section created successfully: %s", section.id_.value)

        return CreateSectionResponse(id=section.id_.value)
