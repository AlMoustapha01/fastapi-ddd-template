"""Update section details command (status, name, description)."""

import logging
from dataclasses import dataclass
from typing import TypedDict
from uuid import UUID

from core.lib.db.flusher import Flusher
from core.lib.db.transaction_manager import TransactionManager
from modules.rules.domain.entities.section import Section
from modules.rules.domain.exceptions import SectionNotFoundError
from modules.rules.domain.ports import SectionRepositoryPort
from modules.rules.domain.value_objects import SectionId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateSectionRequest:
    """Request to update section details."""

    id: UUID
    name: str | None = None
    description: str | None = None


class UpdateSectionResponse(TypedDict):
    """Response for update section details."""

    id: UUID


class UpdateSectionCommand:
    """Command to update section details (status, name, description)."""

    def __init__(
        self,
        section_repository: SectionRepositoryPort,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._section_repository = section_repository
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(self, request: UpdateSectionRequest) -> UpdateSectionResponse:
        log.info("Updating section: %s", request.id)

        section_id = SectionId(request.id)
        section: Section | None = await self._section_repository.find_one_by_id(
            section_id
        )

        if section is None:
            log.warning("Section not found: %s", request.id)
            raise SectionNotFoundError(str(request.id))

        if request.name is not None:
            section.update_name(request.name)

        if request.description is not None:
            section.update_description(request.description)

        await self._section_repository.save(section)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        log.info(
            f"Section updated successfully: id={request.id}, "
            f"name={section.props.name}, "
            f"description={section.props.description}, "
        )

        return UpdateSectionResponse(
            id=section.id_.value,
        )
