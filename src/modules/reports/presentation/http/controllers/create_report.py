"""Create report HTTP controller."""

from inspect import getdoc
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Depends, Request, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict, Field

from core.lib.http.translators import (
    DomainErrorTranslator,
    ServiceUnavailableTranslator,
)
from modules.auth.application.dependencies import require_roles
from modules.auth.domain import AuthUser
from modules.reports.application.commands import (
    CreateReportCommand,
    CreateReportRequest,
    CreateReportResponse,
)
from modules.reports.domain.exceptions import (
    ReportAlreadyExistsError,
    ReportValidationError,
)
from modules.reports.domain.value_objects import ReportConfigProps
from modules.rules.domain.enums import BalanceType, ProfileType


class ReportConfigPydantic(BaseModel):
    """Pydantic model for report configuration."""

    model_config = ConfigDict(frozen=True)

    initial_credit_rule_id: str = Field(..., description="Initial credit rule ID")
    final_credit_rule_id: str = Field(..., description="Final credit rule ID")
    recharge_rules_ids: list[str] = Field(
        ..., min_length=1, description="Recharge rule IDs"
    )
    consumption_rules_ids: list[str] = Field(
        ..., min_length=1, description="Consumption rule IDs"
    )


class CreateReportRequestPydantic(BaseModel):
    """
    Pydantic model for create report request.
    Used to render OpenAPI schema in Swagger UI.
    """

    model_config = ConfigDict(frozen=True)

    title: str = Field(..., min_length=1, max_length=255, description="Report title")
    description: str = Field("", max_length=1000, description="Report description")
    profile_type: ProfileType = Field(..., description="Profile type")
    balance_type: BalanceType = Field(..., description="Balance type")
    config: ReportConfigPydantic = Field(..., description="Report configuration")


def create_create_report_router() -> APIRouter:
    """Create router for report creation endpoint."""
    router = ErrorAwareRouter()

    @router.post(
        "/",
        description=getdoc(CreateReportCommand),
        error_map={
            ReportValidationError: rule(
                status=status.HTTP_400_BAD_REQUEST,
                translator=DomainErrorTranslator(),
            ),
            ReportAlreadyExistsError: rule(
                status=status.HTTP_409_CONFLICT,
                translator=DomainErrorTranslator(),
            ),
            Exception: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
            ),
        },
        status_code=status.HTTP_201_CREATED,
        response_model=CreateReportResponse,
    )
    @inject
    async def create_report(
        request_data_pydantic: CreateReportRequestPydantic,
        command: FromDishka[CreateReportCommand],
        request: Request,
        _: Annotated[AuthUser, Depends(require_roles(["perm_create_report"]))],
    ) -> CreateReportResponse:
        """
        Create a new report.

        Args:
            request_data_pydantic: Report creation data
            command: Injected CreateReportCommand

        Returns:
            CreateReportResponse with the created report ID

        Raises:
            ReportAlreadyExistsError: When a report with the same title exists
            ReportValidationError: When validation fails
        """
        config = ReportConfigProps(
            initial_credit_rule_id=request_data_pydantic.config.initial_credit_rule_id,
            final_credit_rule_id=request_data_pydantic.config.final_credit_rule_id,
            recharge_rules_ids=request_data_pydantic.config.recharge_rules_ids,
            consumption_rules_ids=request_data_pydantic.config.consumption_rules_ids,
        )

        request_data = CreateReportRequest(
            title=request_data_pydantic.title,
            description=request_data_pydantic.description,
            profile_type=request_data_pydantic.profile_type,
            balance_type=request_data_pydantic.balance_type,
            config=config,
            created_by=request.state.db_user.id_.value,
        )
        return await command.execute(request_data)

    return router
