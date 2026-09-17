"""Make section inactive command."""

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
class MakeInactiveSectionRequest:
    """Request to deactivate a section."""

    id: UUID


class MakeInactiveSectionResponse(TypedDict):
    """Response for deactivate section."""

    id: UUID
    status: str


class MakeInactiveSectionCommand:
    """Command to deactivate a section."""

    def __init__(
        self,
        section_repository: SectionRepositoryPort,
        flusher: Flusher,
        transaction_manager: TransactionManager,
    ) -> None:
        self._section_repository = section_repository
        self._flusher = flusher
        self._transaction_manager = transaction_manager

    async def execute(
        self, request: MakeInactiveSectionRequest
    ) -> MakeInactiveSectionResponse:
        """
        Execute the deactivate section command.

        :param request: The deactivation request
        :return: Response with deactivated section ID and status
        :raises SectionNotFoundError: When section is not found
        """
        log.info("Deactivating section: %s", request.id)

        section_id = SectionId(request.id)
        section: Section | None = await self._section_repository.find_one_by_id(
            section_id
        )

        if section is None:
            log.warning("Section not found: %s", request.id)
            raise SectionNotFoundError(str(request.id))

        section.make_inactive()

        await self._section_repository.save(section)
        await self._flusher.flush()
        await self._transaction_manager.commit()

        log.info("Section deactivated successfully: %s", request.id)

        return MakeInactiveSectionResponse(
            id=section.id_.value,
            status=section.props.status.value,
        )
