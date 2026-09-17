from dishka import Provider, Scope, from_context, provide
from pydantic import BaseModel, Field

from core.config.app import AppSettings
from core.config.database.config import PostgresSettings, SqlaEngineSettings
from core.config.keycloak import KeycloakAdminSettings, KeycloakSettings
from core.config.loader import ValidEnvs, get_current_env, load_full_config
from core.config.logs import LoggingSettings
from core.config.security import SecuritySettings


class Settings(BaseModel):
    """
    Main settings container that maps TOML sections to Pydantic models.

    This is where the association between TOML section names and Python classes happens:
    - The attribute name (e.g., 'postgres') matches the TOML section name [postgres]
    - The type annotation (e.g., PostgresSettings) defines which Pydantic model to use

    Mapping mechanism:
    1. load_full_config() loads and merges TOML files into a dictionary:
       {
         "app": {...},
         "postgres": {...},
         "kc_app": {...},
         "kc_admin": {...},
         ...
       }

    2. Settings.model_validate(raw_config) maps each dictionary key to an attribute:
       - raw_config["postgres"] → Settings.postgres (PostgresSettings)
       - raw_config["kc_app"] → Settings.keycloak (KeycloakSettings)
       - raw_config["kc_admin"] → Settings.keycloak_admin (KeycloakAdminSettings)

    3. Pydantic uses Field aliases inside each model to map UPPERCASE keys to lowercase:
       - raw_config["kc_app"]["HOSTNAME"] → KeycloakSettings.hostname

    Example:
        TOML: [kc_app] HOSTNAME="localhost"
        →  raw_config = {"kc_app": {"HOSTNAME": "localhost"}}
        →  Settings(keycloak=KeycloakSettings(...))
        →  settings.keycloak.hostname = "localhost"
    """

    app: AppSettings  # Maps to [app] section
    postgres: PostgresSettings  # Maps to [postgres] section
    sqla: SqlaEngineSettings  # Maps to [sqla] section
    keycloak: KeycloakSettings = Field(alias="kc_app")  # Maps to [kc_app] section
    keycloak_admin: KeycloakAdminSettings = Field(
        alias="kc_admin"
    )  # Maps to [kc_admin]
    security: SecuritySettings  # Maps to [security] section
    logs: LoggingSettings  # Maps to [logs] section


def load_settings(env: ValidEnvs | None = None) -> Settings:
    if env is None:
        env = get_current_env()
    raw_config = load_full_config(env=env)
    return Settings.model_validate(raw_config)


class SettingsProvider(Provider):
    scope = Scope.APP

    settings = from_context(Settings)

    @provide
    def postgres(self, settings: Settings) -> PostgresSettings:
        return settings.postgres

    @provide
    def sqla_engine(self, settings: Settings) -> SqlaEngineSettings:
        return settings.sqla

    @provide
    def keycloak(self, settings: Settings) -> KeycloakSettings:
        return settings.keycloak

    @provide
    def keycloak_admin(self, settings: Settings) -> KeycloakAdminSettings:
        return settings.keycloak_admin

    @provide
    def security(self, settings: Settings) -> SecuritySettings:
        return settings.security

    @provide
    def logs(self, settings: Settings) -> LoggingSettings:
        return settings.logs
