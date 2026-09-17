"""Application settings read from environment variables and an optional `.env`."""

from enum import StrEnum

from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Environment(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AppSettings(BaseModel):
    name: str = "FastAPI DDD Template"
    version: str = "0.1.0"
    environment: Environment = Environment.LOCAL
    docs_enabled: bool = True


class DatabaseSettings(BaseModel):
    host: str = "localhost"
    port: int = Field(default=5432, ge=1, le=65535)
    user: str = "postgres"
    password: SecretStr
    name: str = "app"
    driver: str = "psycopg"
    pool_size: int = Field(default=10, ge=1)
    max_overflow: int = Field(default=10, ge=0)
    echo: bool = False
    echo_pool: bool = False

    @property
    def url(self) -> URL:
        return URL.create(
            drivername=f"postgresql+{self.driver}",
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.name,
        )


class CorsSettings(BaseModel):
    allow_origins: list[str] = Field(default_factory=list)


class LogSettings(BaseModel):
    level: LogLevel = LogLevel.INFO


class Settings(BaseSettings):
    """Root settings: a nested field maps to `SECTION__FIELD` (`DATABASE__HOST`)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app: AppSettings = Field(default_factory=AppSettings)
    database: DatabaseSettings
    cors: CorsSettings = Field(default_factory=CorsSettings)
    log: LogSettings = Field(default_factory=LogSettings)
