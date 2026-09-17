"""Update report HTTP controller."""

from inspect import getdoc
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Path, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field

from core.lib.http.translators import (
    DomainErrorTranslator,
    ServiceUnavailableTranslator,
)
from modules.auth.application.dependencies import require_roles
from modules.auth.domain.user import AuthUser
from modules.reports.application.commands import (
    UpdateReportCommand,
    UpdateReportRequest,
    UpdateReportResponse,
)
from modules.reports.domain.exceptions import (
    ReportNotFoundError,
    ReportValidationError,
)
from modules.reports.domain.value_objects import ReportConfigProps


class ReportConfigUpdatePydantic(BaseModel):
    """Pydantic model for report configuration update."""

    model_config = ConfigDict(frozen=True)

    initial_credit_rule_id: str = Field(..., description="Initial credit rule ID")
    final_credit_rule_id: str = Field(..., description="Final credit rule ID")
    recharge_rules_ids: list[str] = Field(
        ..., min_length=1, description="Recharge rule IDs"
    )
    consumption_rules_ids: list[str] = Field(
        ..., min_length=1, description="Consumption rule IDs"
    )


class UpdateReportRequestPydantic(BaseModel):
    """
    Pydantic model for update report request.
    Used to render OpenAPI schema in Swagger UI.
    """

    model_config = ConfigDict(frozen=True)

    title: str | None = Field(
        None, min_length=1, max_length=255, description="Report title"
    )
    description: str | None = Field(
        None, max_length=1000, description="Report description"
    )
    config: ReportConfigUpdatePydantic | None = Field(
        None, description="Report configuration"
    )


def create_update_report_router() -> APIRouter:
    """Create router for report update endpoint."""
    router = ErrorAwareRouter()

    @router.patch(
        "/{report_id}",
        description=getdoc(UpdateReportCommand),
        error_map={
            ReportValidationError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=DomainErrorTranslator(),
            ),
            ReportNotFoundError: rule(
                status=status.HTTP_404_NOT_FOUND,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_200_OK,
        response_model=UpdateReportResponse,
    )
    @inject
    async def update_report(
        request_data_pydantic: UpdateReportRequestPydantic,
        command: FromDishka[UpdateReportCommand],
        _: Annotated[AuthUser, Depends(require_roles(["perm_update_report"]))],
        report_id: Annotated[UUID, Path(description="Report ID")],
    ) -> UpdateReportResponse:
        """
        Update an existing report.

        Args:
            request_data_pydantic: Report update data
            command: Injected UpdateReportCommand
            report_id: The report ID

        Returns:
            UpdateReportResponse with the updated report ID

        Raises:
            ReportNotFoundError: When the report is not found
            ReportValidationError: When validation fails
        """
        config = None
        if request_data_pydantic.config is not None:
            config = ReportConfigProps(
                initial_credit_rule_id=request_data_pydantic.config.initial_credit_rule_id,
                final_credit_rule_id=request_data_pydantic.config.final_credit_rule_id,
                recharge_rules_ids=request_data_pydantic.config.recharge_rules_ids,
                consumption_rules_ids=request_data_pydantic.config.consumption_rules_ids,
            )

        request_data = UpdateReportRequest(
            id=report_id,
            title=request_data_pydantic.title,
            description=request_data_pydantic.description,
            config=config,
        )
        return await command.execute(request_data)

    return router
