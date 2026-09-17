"""Delete section command."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.lib.db.transaction_manager import TransactionManager
from modules.rules.domain.entities.section import Section
from modules.rules.domain.exceptions import SectionNotFoundError
from modules.rules.domain.ports import SectionRepositoryPort
from modules.rules.domain.value_objects import SectionId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteSectionRequest:
    """Request to delete a section."""

    id: UUID


class DeleteSectionCommand:
    """Command to delete a section."""

    def __init__(
        self,
        section_repository: SectionRepositoryPort,
        transaction_manager: TransactionManager,
    ) -> None:
        self._section_repository = section_repository
        self._transaction_manager = transaction_manager

    async def execute(self, request: DeleteSectionRequest) -> None:
        """
        Execute the delete section command.

        :param request: The section deletion request
        :raises SectionNotFoundError: When section is not found
        """
        log.info("Deleting section: %s", request.id)

        # Find section
        section_id = SectionId(request.id)
        section: Section | None = await self._section_repository.find_one_by_id(
            section_id
        )

        if section is None:
            log.warning("Section not found: %s", request.id)
            raise SectionNotFoundError(str(request.id))

        # Delete section
        await self._section_repository.delete(section)

        # Commit transaction
        await self._transaction_manager.commit()

        log.info("Section deleted successfully: %s", request.id)
