"""Dishka provider for users module."""

from dishka import Provider, Scope, provide, provide_all

from core.lib.db.flusher import Flusher
from core.lib.db.main_transaction_manager_sqla import SqlaMainTransactionManager
from core.lib.db.transaction_manager import TransactionManager
from core.services import UserRepositoryProtocol
from modules.users.application.commands import (
    CreateUserCommand,
    DeleteUserCommand,
    InviteUserCommand,
    MakeActiveUserCommand,
    MakeInactiveUserCommand,
    SqlaUserFlusher,
    UpdateUserCommand,
)
from modules.users.application.queries import (
    ExportUsersQuery,
    GetUserByIdQuery,
    GetUserByKeycloakIdQuery,
    GetUsersQuery,
)
from modules.users.domain.ports import UserRepositoryPort
from modules.users.infrastructure.mappers import UserMapper
from modules.users.infrastructure.repositories import UserRepository


class UsersProvider(Provider):
    """Provider for users module dependencies."""

    scope = Scope.REQUEST

    # Mappers
    mapper = provide(UserMapper)

    # Transaction Manager and Flusher
    tx_manager = provide(SqlaMainTransactionManager, provides=TransactionManager)
    flusher = provide(SqlaUserFlusher, provides=Flusher)

    # Repositories - provide both Port and Protocol
    @provide
    def provide_user_repository(self, repo: UserRepository) -> UserRepositoryPort:
        """Provide UserRepositoryPort."""
        return repo

    @provide
    def provide_user_repository_protocol(
        self, repo: UserRepository
    ) -> UserRepositoryProtocol:
        """Provide UserRepositoryProtocol for core services."""
        return repo

    user_repository = provide(UserRepository)

    # Commands
    commands = provide_all(
        CreateUserCommand,
        UpdateUserCommand,
        MakeActiveUserCommand,
        MakeInactiveUserCommand,
        DeleteUserCommand,
        InviteUserCommand,
    )

    # Queries
    queries = provide_all(
        ExportUsersQuery,
        GetUserByIdQuery,
        GetUserByKeycloakIdQuery,
        GetUsersQuery,
    )
