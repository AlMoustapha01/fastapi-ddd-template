# FastAPI DDD Boilerplate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformer le repo en boilerplate FastAPI générique (DDD / Clean Architecture / CQRS) sans aucune trace du projet précédent, avec deux modules d'exemple liés (`projects`, `tasks`) et tous les problèmes identifiés corrigés.

**Architecture:** Monolithe modulaire. `core` (shared kernel : briques DDD, pagination, UnitOfWork + bus d'événements in-process, SQLAlchemy, erreurs RFC 9457) ; `modules/<nom>` découpés en `domain` / `application` / `infrastructure` / `presentation` ; `app` est la racine de composition (factory FastAPI, providers Dishka, routage, câblage des événements). Les événements de domaine sont publiés dans la transaction par le UnitOfWork ; `tasks` interroge `projects` uniquement via `modules.projects.public`.

**Tech Stack:** Python 3.13, uv, FastAPI, Dishka, SQLAlchemy 2 async + psycopg 3, Alembic (config pyproject), pydantic-settings, pytest + pytest-asyncio + testcontainers, ruff, mypy strict, slotscheck, import-linter, Docker Compose, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-17-fastapi-boilerplate-design.md`

## Global Constraints

- Branche de travail : `chore/generic-boilerplate`. Un commit par tâche, message conventionnel, terminé par la ligne `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>` (passer un second `-m`).
- Toutes les commandes passent par `uv run` (ou `make`, qui l'utilise).
- Python `>=3.13` ; syntaxe de génériques PEP 695 (`class Page[T]`), jamais `Generic[T]` (ruff UP046).
- Ruff : `line-length = 88`, `preview = true`, jeu de règles du `pyproject.toml` (Task 1). `RUF029` est ignoré. Pas d'import hors top-level (PLC0415). Pas d'`assert` dans `src/`.
- mypy `strict = true` sur `src`, `tests`, `scripts`, `migrations` (hors `migrations/versions`).
- Avant chaque commit : `make format` puis `make lint` doivent passer ; les tests de la tâche doivent passer.
- Les valeurs d'énumérations exposées par l'API sont en minuscules : `active`/`archived`, `todo`/`in_progress`/`done`/`cancelled`.
- Mapping erreurs → HTTP : `NotFoundError` 404, `ConflictError` 409, `BusinessRuleViolationError` 409, `DomainValidationError` 422, autre `DomainError` 400, validation de requête 422 (`code = "request_validation_error"`), exception inattendue 500 (`code = "internal_error"`). Corps `application/problem+json` : `type`, `title`, `status`, `detail?`, `code?`, `details?`, `errors?`.
- Les handlers d'événements n'appellent jamais `commit()`.
- Aucun module n'importe un autre module ailleurs que via `modules.<autre>.public`. `core` n'importe jamais `app` ni `modules`.
- **Écart assumé vs spec 5.2 :** les primitives de pagination vivent dans `core/domain/pagination.py` (et non `core/application/`), car les ports de repository (couche domaine) en dépendent et le domaine ne doit pas importer l'application.
- Tests unitaires : `tests/unit/` (aucune I/O). Tests d'intégration : `tests/integration/` (marqués automatiquement `integration`, Docker requis).

## Carte des fichiers (état final)

```
.dockerignore  .env.example  .gitignore  .pre-commit-config.yaml  Dockerfile  Makefile
README.md  docker-compose.yaml  pyproject.toml  uv.lock
.github/workflows/ci.yaml
migrations/env.py  migrations/script.py.mako  migrations/versions/2026_09_17_1200-0001_initial_schema.py
scripts/dishka/plot_dependencies_data.py
src/app/{__init__,main,lifespan,routers,providers,event_handlers,models}.py
src/core/domain/{__init__,errors,value_object,identifier,entity,aggregate_root,events,pagination}.py
src/core/application/{__init__,unit_of_work,event_bus}.py
src/core/infrastructure/{__init__,settings,logs,provider}.py
src/core/infrastructure/db/{__init__,base,mixins,mapper,query,repository,tracker,errors,unit_of_work,provider}.py
src/core/infrastructure/events/{__init__,in_process_bus}.py
src/core/presentation/{__init__}.py  src/core/presentation/http/{__init__,errors,pagination,health}.py
src/modules/projects/{__init__,public,provider}.py
src/modules/projects/domain/{__init__,enums,errors,events}.py
src/modules/projects/domain/value_objects/{__init__,project_id,project_name,project_description}.py
src/modules/projects/domain/entities/{__init__,project}.py
src/modules/projects/domain/ports/{__init__,project_repository}.py
src/modules/projects/application/{__init__,dto}.py
src/modules/projects/application/commands/{__init__,create_project,update_project,archive_project,delete_project}.py
src/modules/projects/application/queries/{__init__,get_project_by_id,list_projects}.py
src/modules/projects/infrastructure/{__init__}.py + models/ mappers/ repositories/ ({__init__, project_*}.py)
src/modules/projects/presentation/{__init__}.py  presentation/http/{__init__,schemas,router}.py
src/modules/projects/presentation/http/controllers/{__init__,create_project,list_projects,get_project,update_project,archive_project,delete_project}.py
src/modules/tasks/... (même anatomie ; + domain/ports/project_lookup.py,
  application/event_handlers/{__init__,cancel_tasks_on_project_archived,delete_tasks_on_project_deleted}.py,
  infrastructure/adapters/{__init__,projects_lookup}.py,
  controllers/{create_task,list_tasks,get_task,update_task,change_task_status,delete_task}.py)
tests/{__init__,conftest}.py
tests/fakes/{__init__,unit_of_work,projects,tasks}.py
tests/unit/{__init__}.py
tests/unit/core/{__init__,samples,test_settings,test_logs,test_domain_building_blocks,test_pagination,test_event_handler_registry,test_tracker,test_in_process_bus,test_unit_of_work,test_query}.py
tests/unit/app/{__init__,test_app}.py
tests/unit/projects/{__init__,factories,test_project_domain,test_project_use_cases}.py
tests/unit/tasks/{__init__,factories,test_task_domain,test_task_use_cases}.py
tests/integration/{__init__,conftest,test_infrastructure}.py
tests/integration/projects/{__init__,test_project_repository,test_projects_api}.py
tests/integration/tasks/{__init__,test_task_repository,test_project_events,test_tasks_api}.py
```

Supprimés : `AUTHENTICATION.md`, `alembic.ini`, `config/`, `scripts/makefile/`, ancien `src/`, ancien `tests/`, ancienne CI, `.DS_Store`.

---

### Task 1: Table rase et outillage

**Files:**
- Delete: `src/app/`, `src/core/`, `src/modules/`, `tests/`, `config/`, `scripts/`, `.github/`, `AUTHENTICATION.md`, `alembic.ini`
- Modify: `pyproject.toml`, `.gitignore`, `.pre-commit-config.yaml`, `README.md`, `uv.lock`
- Create: `Makefile` (remplacé), `src/app/__init__.py`, `src/core/__init__.py`, `src/modules/__init__.py`, `tests/__init__.py`, `tests/conftest.py`

**Interfaces:**
- Consumes: rien.
- Produces: packages vides `app`, `core`, `modules` importables ; `make format`, `make lint` (sans import-linter pour l'instant), `make test`, `make test.unit` ; marqueur pytest `integration` appliqué automatiquement à `tests/integration/**`.

- [ ] **Step 1: Supprimer l'ancien projet**

```bash
git rm -r -q src/app src/core src/modules tests config scripts .github AUTHENTICATION.md alembic.ini
find . -name .DS_Store -not -path "./.venv/*" -delete
```

- [ ] **Step 2: Mettre à jour les dépendances avec uv**

```bash
uv remove alembic-postgresql-enum fastapi-error-map httpx keyof openpyxl python-jose python-slugify sqlalchemy uvicorn uvloop
uv remove --group test line-profiler
uv add "sqlalchemy[asyncio]" "uvicorn[standard]" pydantic pydantic-settings
uv add --group dev import-linter
uv add --group test "testcontainers[postgres]"
```

Vérifier dans `pyproject.toml` : `dependencies` = alembic, dishka, fastapi, psycopg[binary], pydantic, pydantic-settings, sqlalchemy[asyncio], uuid-utils, uvicorn[standard] ; groupe `dev` = mypy, pre-commit, ruff, slotscheck, import-linter, `{ include-group = "test" }` ; groupe `test` = coverage, httpx, pytest, pytest-asyncio, testcontainers[postgres].

- [ ] **Step 3: Réécrire les métadonnées et la config outils de `pyproject.toml`**

Ne pas toucher aux listes `dependencies` et `[dependency-groups]` écrites par uv. Remplacer le haut du fichier jusqu'à `dependencies = [` exclu par :

```toml
[build-system]
requires = ["hatchling>=1.13"]
build-backend = "hatchling.build"

[tool.hatch.build]
sources = ["src"]

[tool.hatch.build.targets.wheel]
packages = ["src/app", "src/core", "src/modules"]

[project]
name = "fastapi-ddd-template"
version = "0.1.0"
description = "FastAPI boilerplate following Domain-Driven Design, Clean Architecture and CQRS"
readme = "README.md"
authors = [
    { name = "Doumbia Al Moustapha", email = "doumbialmoustapha@gmail.com" },
]
requires-python = ">=3.13"
```

Puis remplacer tout ce qui suit `[dependency-groups]` (de `[tool.coverage.report]` jusqu'à la fin, y compris l'ancienne section `[tool.alembic]`) par :

```toml
[tool.coverage.report]
show_missing = true
skip_empty = true
exclude_also = [
    "if __name__ == .__main__.:",
    '@(abc\.)?abstractmethod',
    '\.\.\.',
]

[tool.coverage.run]
source = ["src"]
omit = ["**/__init__.py"]
concurrency = ["thread"]
parallel = true
branch = true

[tool.mypy]
files = ["src", "tests"]
strict = true
ignore_missing_imports = true
allow_subclassing_any = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false
disallow_incomplete_defs = false

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
markers = [
    "integration: needs Docker (PostgreSQL is started with testcontainers)",
]

[tool.ruff]
line-length = 88
preview = true
src = ["src", "."]

[tool.ruff.format]
skip-magic-trailing-comma = false

[tool.ruff.lint]
select = [
    "A", "ARG", "ASYNC", "B", "C4", "C90", "DTZ", "E", "ERA001", "F", "FLY", "I",
    "LOG", "N", "PERF", "PL", "PT", "PTH", "Q", "RET", "RSE", "RUF", "S", "SIM",
    "SLF", "SLOT", "T20", "TCH", "TID", "UP", "W",
]
ignore = [
    "N818",    # error-suffix-on-exception-name
    "PLR0913", # too-many-arguments
    "PLR0917", # too-many-positional-arguments
    "PLR6301", # no-self-use
    "PTH123",  # builtin-open
    "RUF029",  # unused-async: endpoints and port implementations may not await
    "TC001",   # typing-only-first-party-import
    "TC002",   # typing-only-third-party-import
    "TC003",   # typing-only-standard-library-import
    "TC006",   # runtime-cast-value
    "UP015",   # redundant-open-modes
]

[tool.ruff.lint.per-file-ignores]
"migrations/versions/**" = ["ALL"]
"scripts/**" = ["T201"]
"tests/**" = ["S101", "PLR2004"]

[tool.ruff.lint.isort]
combine-as-imports = true
force-wrap-aliases = true
split-on-trailing-comma = true

[tool.slotscheck]
strict-imports = false
```

- [ ] **Step 4: Remplacer `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[oc]
build/
dist/
wheels/
*.egg-info

# Virtual environment and local configuration
.venv
.env

# Tooling
.coverage
.coverage.*
htmlcov/
.mypy_cache/
.pytest_cache/
.ruff_cache/

# OS
.DS_Store
```

- [ ] **Step 5: Remplacer `.pre-commit-config.yaml`**

```yaml
repos:
  - repo: local
    hooks:
      - id: lint
        name: make lint
        entry: make lint
        language: system
        pass_filenames: false
        always_run: true
```

- [ ] **Step 6: Remplacer `Makefile`** (indentation des recettes par tabulations)

```make
.DEFAULT_GOAL := help
UV := uv run

.PHONY: help install run up down migrate migration format lint test test.unit cov clean deps-graph

help: ## Show available commands
	@grep -E '^[a-zA-Z_.-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

install: ## Install dependencies and create .env from .env.example
	uv sync --group dev
	@test -f .env || cp .env.example .env

run: ## Run the API locally with auto-reload
	$(UV) uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000

up: ## Build and start PostgreSQL and the API with Docker Compose
	docker compose up -d --build

down: ## Stop the Docker Compose stack
	docker compose down

migrate: ## Apply database migrations
	$(UV) alembic upgrade head

migration: ## Generate a migration: make migration m="add something"
	@test -n "$(m)" || (echo 'Usage: make migration m="message"' && exit 1)
	$(UV) alembic revision --autogenerate -m "$(m)"

format: ## Format code and apply safe lint fixes
	$(UV) ruff format
	$(UV) ruff check --fix

lint: ## Run static checks
	$(UV) ruff format --check
	$(UV) ruff check
	$(UV) mypy
	$(UV) slotscheck src

test: ## Run all tests (integration tests need Docker)
	$(UV) pytest

test.unit: ## Run unit tests only
	$(UV) pytest -m "not integration"

cov: ## Run tests with a coverage report
	$(UV) coverage run -m pytest
	$(UV) coverage combine
	$(UV) coverage report

clean: ## Remove caches and build artifacts
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage .coverage.* htmlcov build dist

deps-graph: ## Print the Dishka dependency graph (d2 format)
	$(UV) python scripts/dishka/plot_dependencies_data.py
```

- [ ] **Step 7: Créer les packages vides et la configuration pytest**

Créer vides : `src/app/__init__.py`, `src/core/__init__.py`, `src/modules/__init__.py`, `tests/__init__.py`.

`tests/conftest.py` :

```python
"""Shared pytest configuration."""

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark every test located under `tests/integration/` with `integration`."""
    for item in items:
        if "integration" in item.path.parts:
            item.add_marker(pytest.mark.integration)
```

- [ ] **Step 8: Remplacer `README.md` par une version provisoire** (réécrite en Task 20)

```markdown
# FastAPI DDD Template

FastAPI boilerplate following Domain-Driven Design, Clean Architecture and CQRS.
```

- [ ] **Step 9: Vérifier**

```bash
uv sync --group dev
uv run python -c "import app, core, modules; print('ok')"
make format && make lint
make clean
grep -rniE "prepaid|equation|orange|keycloak|realm" --exclude-dir=.venv --exclude-dir=.git --exclude-dir=docs --exclude=uv.lock . || echo "clean"
```

Expected : `ok`, lint sans erreur, `clean`.

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "chore: remove previous project and reset tooling" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Settings, logging et `.env.example`

**Files:**
- Create: `src/core/infrastructure/__init__.py` (vide), `src/core/infrastructure/settings.py`, `src/core/infrastructure/logs.py`, `.env.example`
- Test: `tests/unit/__init__.py` (vide), `tests/unit/core/__init__.py` (vide), `tests/unit/core/test_settings.py`, `tests/unit/core/test_logs.py`

**Interfaces:**
- Produces:
  - `core.infrastructure.settings` : `Environment(StrEnum)` {LOCAL, TEST, STAGING, PRODUCTION} ; `LogLevel(StrEnum)` {DEBUG, INFO, WARNING, ERROR, CRITICAL} ; `AppSettings(name, version, environment, docs_enabled)` ; `DatabaseSettings(host, port, user, password: SecretStr, name, driver, pool_size, max_overflow, echo, echo_pool)` avec propriété `url -> sqlalchemy.URL` ; `CorsSettings(allow_origins: list[str])` ; `LogSettings(level: LogLevel)` ; `Settings(BaseSettings)` avec champs `app`, `database` (requis), `cors`, `log`.
  - `core.infrastructure.logs` : `HANDLER_NAME: Final[str]`, `configure_logging(level: LogLevel) -> None` (idempotent, ne retire aucun handler existant).

- [ ] **Step 1: Écrire les tests qui échouent**

`tests/unit/core/test_settings.py` :

```python
"""Settings are read from environment variables and an optional `.env` file."""

from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from core.infrastructure.settings import (
    DatabaseSettings,
    Environment,
    LogLevel,
    Settings,
)

VARIABLES = (
    "APP__NAME",
    "APP__ENVIRONMENT",
    "APP__DOCS_ENABLED",
    "DATABASE__HOST",
    "DATABASE__PORT",
    "DATABASE__PASSWORD",
    "CORS__ALLOW_ORIGINS",
    "LOG__LEVEL",
)


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    for name in VARIABLES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)


def test_reads_nested_values_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE__PASSWORD", "secret")
    monkeypatch.setenv("DATABASE__PORT", "6543")
    monkeypatch.setenv("CORS__ALLOW_ORIGINS", '["http://localhost:3000"]')
    monkeypatch.setenv("LOG__LEVEL", "DEBUG")

    settings = Settings()

    assert settings.database.port == 6543
    assert settings.database.password.get_secret_value() == "secret"
    assert settings.cors.allow_origins == ["http://localhost:3000"]
    assert settings.log.level is LogLevel.DEBUG


def test_applies_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE__PASSWORD", "secret")

    settings = Settings()

    assert settings.app.environment is Environment.LOCAL
    assert settings.app.docs_enabled is True
    assert settings.database.host == "localhost"
    assert settings.database.name == "app"
    assert settings.cors.allow_origins == []
    assert settings.log.level is LogLevel.INFO


def test_database_password_is_required() -> None:
    with pytest.raises(ValidationError):
        Settings()


def test_reads_dotenv_file_from_working_directory(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "DATABASE__PASSWORD=from-dotenv\nAPP__NAME=Demo\n", encoding="utf-8"
    )

    settings = Settings()

    assert settings.database.password.get_secret_value() == "from-dotenv"
    assert settings.app.name == "Demo"


def test_database_url_is_built_from_parts() -> None:
    database = DatabaseSettings(
        host="db", port=5433, user="user", password=SecretStr("p@ss"), name="demo"
    )

    url = database.url

    assert url.drivername == "postgresql+psycopg"
    assert (url.host, url.port, url.username, url.database) == (
        "db",
        5433,
        "user",
        "demo",
    )
    assert url.password == "p@ss"
    assert "p@ss" not in str(url)
```

`tests/unit/core/test_logs.py` :

```python
"""Logging configuration is idempotent and keeps existing handlers."""

import logging
from collections.abc import Iterator

import pytest

from core.infrastructure.logs import HANDLER_NAME, configure_logging
from core.infrastructure.settings import LogLevel


@pytest.fixture(autouse=True)
def restore_root_logger() -> Iterator[None]:
    root = logging.getLogger()
    level, handlers = root.level, list(root.handlers)
    yield
    root.setLevel(level)
    root.handlers[:] = handlers


def test_sets_level_and_installs_a_single_handler() -> None:
    configure_logging(LogLevel.DEBUG)
    configure_logging(LogLevel.WARNING)

    root = logging.getLogger()
    assert root.level == logging.WARNING
    assert [handler.get_name() for handler in root.handlers].count(HANDLER_NAME) == 1


def test_keeps_handlers_installed_by_others() -> None:
    other = logging.NullHandler()
    logging.getLogger().addHandler(other)

    configure_logging(LogLevel.INFO)

    assert other in logging.getLogger().handlers
```

- [ ] **Step 2: Vérifier l'échec**

Run: `uv run pytest tests/unit/core -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'core.infrastructure'`).

- [ ] **Step 3: Implémenter**

`src/core/infrastructure/settings.py` :

```python
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
    """Root settings. A nested field maps to `SECTION__FIELD` (e.g. `DATABASE__HOST`)."""

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
```

`src/core/infrastructure/logs.py` :

```python
"""Logging configuration."""

import logging
from typing import Final

from core.infrastructure.settings import LogLevel

HANDLER_NAME: Final[str] = "app-console"
LOG_FORMAT: Final[str] = "%(asctime)s %(levelname)-8s %(name)s - %(message)s"


def configure_logging(level: LogLevel) -> None:
    """Install the console handler once; later calls only update the root level."""
    root = logging.getLogger()
    root.setLevel(level.value)
    if any(handler.get_name() == HANDLER_NAME for handler in root.handlers):
        return
    handler = logging.StreamHandler()
    handler.set_name(HANDLER_NAME)
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(handler)
```

`.env.example` :

```dotenv
# Application
APP__NAME="FastAPI DDD Template"
APP__ENVIRONMENT=local
APP__DOCS_ENABLED=true

# Database
DATABASE__HOST=localhost
DATABASE__PORT=5432
DATABASE__USER=postgres
DATABASE__PASSWORD=postgres
DATABASE__NAME=app

# CORS (JSON list, empty disables CORS)
CORS__ALLOW_ORIGINS=[]

# Logging
LOG__LEVEL=INFO
```

- [ ] **Step 4: Vérifier le succès**

Run: `uv run pytest tests/unit/core -v`
Expected: 7 passed.

- [ ] **Step 5: Lint et commit**

```bash
make format && make lint
git add src/core/infrastructure tests/unit .env.example
git commit -m "feat(core): add pydantic settings and logging configuration" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Briques du domaine

**Files:**
- Create: `src/core/domain/__init__.py` (vide), `src/core/domain/errors.py`, `src/core/domain/value_object.py`, `src/core/domain/identifier.py`, `src/core/domain/entity.py`, `src/core/domain/aggregate_root.py`, `src/core/domain/events.py`
- Test: `tests/unit/core/samples.py`, `tests/unit/core/test_domain_building_blocks.py`

**Interfaces:**
- Produces:
  - `core.domain.errors` : `DomainError(message: str, *, code: str | None = None, details: dict[str, Any] | None = None)` avec attributs `message`, `code` (défaut `default_code` de la classe), `details` ; sous-classes `NotFoundError` (`"not_found"`), `ConflictError` (`"conflict"`), `BusinessRuleViolationError` (`"business_rule_violation"`), `DomainValidationError` (`"validation_error"`). Base : `"domain_error"`.
  - `core.domain.value_object.ValueObject` (dataclass frozen/slots/repr=False).
  - `core.domain.identifier.EntityId(ValueObject)` : champ `value: UUID`, `@classmethod generate() -> Self` (UUID v7).
  - `core.domain.entity.Entity[TId: EntityId, TProps]` : `__init__(*, id_, props, created_at_=None, updated_at_=None)`, propriété en lecture seule `id_`, attributs `props`, `created_at_`, `updated_at_`, `touch() -> None`, abstrait `validate() -> None`.
  - `core.domain.aggregate_root.AggregateRoot[TId, TProps](Entity)` : `record_event(event: DomainEvent) -> None`, `pull_events() -> list[DomainEvent]`.
  - `core.domain.events.DomainEvent` : dataclass frozen/slots/kw_only avec `event_id: UUID` (v7) et `occurred_at: datetime` (UTC).
  - Tests : `tests.unit.core.samples` expose `SampleId`, `SampleProps`, `SampleRenamed`, `SampleAggregate` (`rename(label)`), `make_sample(label="first")`.

- [ ] **Step 1: Écrire le modèle d'exemple et les tests**

`tests/unit/core/samples.py` :

```python
"""Minimal domain model used to test the core building blocks."""

from dataclasses import dataclass

from core.domain.aggregate_root import AggregateRoot
from core.domain.errors import DomainValidationError
from core.domain.events import DomainEvent
from core.domain.identifier import EntityId


@dataclass(frozen=True, slots=True, repr=False)
class SampleId(EntityId):
    """Identifier of `SampleAggregate`."""


@dataclass(slots=True)
class SampleProps:
    label: str


@dataclass(frozen=True, slots=True, kw_only=True)
class SampleRenamed(DomainEvent):
    label: str


class SampleAggregate(AggregateRoot[SampleId, SampleProps]):
    def rename(self, label: str) -> None:
        self.props.label = label
        self.touch()
        self.record_event(SampleRenamed(label=label))

    def validate(self) -> None:
        if not self.props.label:
            raise DomainValidationError("Label is required.", code="invalid_label")


def make_sample(label: str = "first") -> SampleAggregate:
    return SampleAggregate(id_=SampleId.generate(), props=SampleProps(label=label))
```

`tests/unit/core/test_domain_building_blocks.py` :

```python
"""Errors, value objects, entities, aggregates and events."""

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from core.domain.errors import (
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
    DomainValidationError,
    NotFoundError,
)
from core.domain.value_object import ValueObject
from tests.unit.core.samples import (
    SampleAggregate,
    SampleId,
    SampleProps,
    SampleRenamed,
    make_sample,
)

PAST = datetime(2000, 1, 1, tzinfo=UTC)


@dataclass(frozen=True, slots=True, repr=False)
class Money(ValueObject):
    amount: int
    currency: str


class TestDomainErrors:
    def test_exposes_message_code_and_details(self) -> None:
        error = NotFoundError("Missing.", details={"id": "42"})

        assert str(error) == "Missing."
        assert error.message == "Missing."
        assert error.code == "not_found"
        assert error.details == {"id": "42"}

    def test_explicit_code_overrides_the_default(self) -> None:
        assert ConflictError("Taken.", code="name_taken").code == "name_taken"

    @pytest.mark.parametrize(
        ("error_type", "code"),
        [
            (DomainError, "domain_error"),
            (NotFoundError, "not_found"),
            (ConflictError, "conflict"),
            (BusinessRuleViolationError, "business_rule_violation"),
            (DomainValidationError, "validation_error"),
        ],
    )
    def test_default_codes(self, error_type: type[DomainError], code: str) -> None:
        error = error_type("message")

        assert isinstance(error, DomainError)
        assert error.code == code
        assert error.details == {}


class TestValueObject:
    def test_equality_is_structural(self) -> None:
        assert Money(10, "EUR") == Money(10, "EUR")
        assert Money(10, "EUR") != Money(10, "USD")

    def test_is_immutable(self) -> None:
        money = Money(10, "EUR")

        with pytest.raises(AttributeError):
            money.amount = 20  # type: ignore[misc]

    def test_repr_lists_fields(self) -> None:
        assert repr(Money(10, "EUR")) == "Money(amount=10, currency='EUR')"

    def test_base_class_cannot_be_instantiated(self) -> None:
        with pytest.raises(TypeError):
            ValueObject()


class TestEntityId:
    def test_generate_returns_a_uuid7(self) -> None:
        assert SampleId.generate().value.version == 7


class TestEntity:
    def test_equality_uses_type_and_id_only(self) -> None:
        identifier = SampleId.generate()
        first = SampleAggregate(id_=identifier, props=SampleProps(label="a"))
        second = SampleAggregate(id_=identifier, props=SampleProps(label="b"))

        assert first == second
        assert hash(first) == hash(second)
        assert first != make_sample()

    def test_validate_runs_at_construction(self) -> None:
        with pytest.raises(DomainValidationError):
            make_sample(label="")

    def test_updated_at_defaults_to_created_at(self) -> None:
        aggregate = SampleAggregate(
            id_=SampleId.generate(), props=SampleProps(label="a"), created_at_=PAST
        )

        assert aggregate.updated_at_ == PAST

    def test_touch_refreshes_updated_at_only(self) -> None:
        aggregate = SampleAggregate(
            id_=SampleId.generate(), props=SampleProps(label="a"), created_at_=PAST
        )

        aggregate.rename("b")

        assert aggregate.created_at_ == PAST
        assert aggregate.updated_at_ > PAST

    def test_id_is_read_only(self) -> None:
        aggregate = make_sample()

        with pytest.raises(AttributeError):
            aggregate.id_ = SampleId.generate()  # type: ignore[misc]


class TestAggregateRoot:
    def test_pull_events_returns_then_forgets_recorded_events(self) -> None:
        aggregate = make_sample()
        aggregate.rename("second")

        events = aggregate.pull_events()

        assert [type(event) for event in events] == [SampleRenamed]
        assert aggregate.pull_events() == []

    def test_events_have_an_identity_and_a_utc_timestamp(self) -> None:
        event = SampleRenamed(label="x")

        assert event.event_id.version == 7
        assert event.occurred_at.tzinfo is UTC
```

- [ ] **Step 2: Vérifier l'échec**

Run: `uv run pytest tests/unit/core/test_domain_building_blocks.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'core.domain'`).

- [ ] **Step 3: Implémenter**

`src/core/domain/errors.py` :

```python
"""Business error hierarchy. The category decides the HTTP status."""

from typing import Any, ClassVar


class DomainError(Exception):
    """Base class of every error raised by the domain and application layers."""

    default_code: ClassVar[str] = "domain_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.details: dict[str, Any] = details or {}


class NotFoundError(DomainError):
    default_code = "not_found"


class ConflictError(DomainError):
    default_code = "conflict"


class BusinessRuleViolationError(DomainError):
    default_code = "business_rule_violation"


class DomainValidationError(DomainError):
    default_code = "validation_error"
```

`src/core/domain/value_object.py` :

```python
"""Base class for immutable value objects."""

from dataclasses import dataclass, fields
from typing import Any, Self


@dataclass(frozen=True, slots=True, repr=False)
class ValueObject:
    """
    Immutable object defined only by its attributes.

    Decorate subclasses with `@dataclass(frozen=True, slots=True, repr=False)` and
    validate invariants in `__post_init__` by raising `DomainValidationError`.
    Fields declared with `field(repr=False)` are hidden from `repr()`.
    """

    def __new__(cls, *_args: Any, **_kwargs: Any) -> Self:
        if cls is ValueObject:
            raise TypeError("Base ValueObject cannot be instantiated directly.")
        if not fields(cls):
            raise TypeError(f"{cls.__name__} must have at least one field.")
        return object.__new__(cls)

    def __post_init__(self) -> None:
        """Validation hook for subclasses."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._repr_fields()})"

    def _repr_fields(self) -> str:
        visible = [item for item in fields(self) if item.repr]
        if not visible:
            return "<hidden>"
        if len(visible) == 1:
            return repr(getattr(self, visible[0].name))
        return ", ".join(f"{item.name}={getattr(self, item.name)!r}" for item in visible)
```

`src/core/domain/identifier.py` :

```python
"""UUID-based identity value object."""

from dataclasses import dataclass
from typing import Self
from uuid import UUID

import uuid_utils.compat as uuid_utils

from core.domain.value_object import ValueObject


@dataclass(frozen=True, slots=True, repr=False)
class EntityId(ValueObject):
    """Identity of an entity. Subclass it once per aggregate (e.g. `ProjectId`)."""

    value: UUID

    @classmethod
    def generate(cls) -> Self:
        return cls(uuid_utils.uuid7())
```

`src/core/domain/events.py` :

```python
"""Base class for domain events."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID

import uuid_utils.compat as uuid_utils


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    """Immutable record of something meaningful that happened in the domain."""

    event_id: UUID = field(default_factory=uuid_utils.uuid7)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
```

`src/core/domain/entity.py` :

```python
"""Base class for domain entities."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime

from core.domain.identifier import EntityId


class Entity[TId: EntityId, TProps](ABC):
    """
    Object defined by its identity rather than by its attributes.

    - `id_` is read-only; entities are compared by type and `id_`.
    - `props` holds the mutable state; mutating methods must call `touch()`.
    - `validate()` runs once, at construction.
    """

    def __init__(
        self,
        *,
        id_: TId,
        props: TProps,
        created_at_: datetime | None = None,
        updated_at_: datetime | None = None,
    ) -> None:
        self._id = id_
        self.props = props
        self.created_at_ = created_at_ or datetime.now(tz=UTC)
        self.updated_at_ = updated_at_ or self.created_at_
        self.validate()

    @property
    def id_(self) -> TId:
        return self._id

    def touch(self) -> None:
        """Record that the state of the entity changed."""
        self.updated_at_ = datetime.now(tz=UTC)

    @abstractmethod
    def validate(self) -> None:
        """Raise a `DomainError` when an invariant does not hold."""

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Entity)
            and type(self) is type(other)
            and self.id_ == other.id_
        )

    def __hash__(self) -> int:
        return hash((type(self), self._id))
```

`src/core/domain/aggregate_root.py` :

```python
"""Aggregate root: consistency boundary that records domain events."""

from datetime import datetime

from core.domain.entity import Entity
from core.domain.events import DomainEvent
from core.domain.identifier import EntityId


class AggregateRoot[TId: EntityId, TProps](Entity[TId, TProps]):
    """Entity whose recorded events are published when its unit of work commits."""

    def __init__(
        self,
        *,
        id_: TId,
        props: TProps,
        created_at_: datetime | None = None,
        updated_at_: datetime | None = None,
    ) -> None:
        self._events: list[DomainEvent] = []
        super().__init__(
            id_=id_, props=props, created_at_=created_at_, updated_at_=updated_at_
        )

    def record_event(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        """Return the recorded events and forget them."""
        events, self._events = self._events, []
        return events
```

- [ ] **Step 4: Vérifier le succès**

Run: `uv run pytest tests/unit/core/test_domain_building_blocks.py -v`
Expected: 19 passed.

- [ ] **Step 5: Lint et commit**

```bash
make format && make lint
git add src/core/domain tests/unit/core
git commit -m "feat(core): add domain building blocks" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Pagination et ports applicatifs

**Files:**
- Create: `src/core/domain/pagination.py`, `src/core/application/__init__.py` (vide), `src/core/application/unit_of_work.py`, `src/core/application/event_bus.py`
- Test: `tests/unit/core/test_pagination.py`, `tests/unit/core/test_event_handler_registry.py`

**Interfaces:**
- Consumes: `DomainValidationError`, `DomainEvent` (Task 3).
- Produces:
  - `core.domain.pagination` : `MAX_PAGE_SIZE = 100` ; `SortDirection(StrEnum)` {ASC="asc", DESC="desc"} ; `Sort(field: str, direction: SortDirection = ASC)` avec `Sort.parse(raw: str) -> Sort` (`"-name"` → DESC) ; `PageParams(page: int = 1, size: int = 20)` validé, propriété `offset` ; `Page[T](items: Sequence[T], total: int, page: int, size: int)` avec propriété `pages` et `map(transform) -> Page[U]`.
  - `core.application.unit_of_work.UnitOfWork` (Protocol) : `async commit() -> None`, `async rollback() -> None`.
  - `core.application.event_bus` : `EventHandler[TEvent: DomainEvent]` (Protocol, `async handle(event) -> None`) ; `EventBus` (Protocol, `async publish(event: DomainEvent) -> None`) ; `EventHandlerRegistry(handlers: Mapping[type[DomainEvent], Sequence[type[EventHandler[Any]]]] = {})` avec `handlers_for(event) -> Sequence[type[EventHandler[Any]]]` (correspondance de type exacte).

- [ ] **Step 1: Écrire les tests qui échouent**

`tests/unit/core/test_pagination.py` :

```python
"""Pagination and sorting primitives."""

import pytest

from core.domain.errors import DomainValidationError
from core.domain.pagination import (
    MAX_PAGE_SIZE,
    Page,
    PageParams,
    Sort,
    SortDirection,
)


class TestSort:
    def test_parses_ascending_field(self) -> None:
        assert Sort.parse("name") == Sort("name", SortDirection.ASC)

    def test_parses_descending_field(self) -> None:
        assert Sort.parse("-created_at") == Sort("created_at", SortDirection.DESC)

    @pytest.mark.parametrize("raw", ["", "-", "   "])
    def test_rejects_empty_field(self, raw: str) -> None:
        with pytest.raises(DomainValidationError) as exc_info:
            Sort.parse(raw)

        assert exc_info.value.code == "invalid_sort_field"


class TestPageParams:
    def test_offset(self) -> None:
        assert PageParams(page=3, size=20).offset == 40

    @pytest.mark.parametrize(
        ("page", "size", "code"),
        [
            (0, 20, "invalid_page"),
            (1, 0, "invalid_page_size"),
            (1, MAX_PAGE_SIZE + 1, "invalid_page_size"),
        ],
    )
    def test_rejects_out_of_range_values(self, page: int, size: int, code: str) -> None:
        with pytest.raises(DomainValidationError) as exc_info:
            PageParams(page=page, size=size)

        assert exc_info.value.code == code


class TestPage:
    @pytest.mark.parametrize(
        ("total", "size", "pages"), [(0, 20, 0), (20, 20, 1), (21, 20, 2), (5, 0, 0)]
    )
    def test_pages(self, total: int, size: int, pages: int) -> None:
        assert Page[int](items=[], total=total, page=1, size=size).pages == pages

    def test_map_transforms_items_and_keeps_metadata(self) -> None:
        page = Page[int](items=[1, 2], total=5, page=2, size=2)

        assert page.map(str) == Page[str](items=["1", "2"], total=5, page=2, size=2)
```

`tests/unit/core/test_event_handler_registry.py` :

```python
"""Registry mapping event types to handler types."""

from core.application.event_bus import EventHandlerRegistry
from core.domain.events import DomainEvent
from tests.unit.core.samples import SampleRenamed


class RecordingHandler:
    def __init__(self) -> None:
        self.received: list[DomainEvent] = []

    async def handle(self, event: SampleRenamed) -> None:
        self.received.append(event)


class OtherRecordingHandler(RecordingHandler):
    """A second handler type."""


def test_returns_registered_handlers_in_order() -> None:
    registry = EventHandlerRegistry(
        handlers={SampleRenamed: (RecordingHandler, OtherRecordingHandler)}
    )

    handlers = registry.handlers_for(SampleRenamed(label="x"))

    assert handlers == (RecordingHandler, OtherRecordingHandler)


def test_unregistered_event_has_no_handler() -> None:
    assert EventHandlerRegistry().handlers_for(SampleRenamed(label="x")) == ()
```

- [ ] **Step 2: Vérifier l'échec**

Run: `uv run pytest tests/unit/core/test_pagination.py tests/unit/core/test_event_handler_registry.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implémenter**

`src/core/domain/pagination.py` :

```python
"""Framework-agnostic pagination and sorting primitives."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import ceil
from typing import Final, Self

from core.domain.errors import DomainValidationError

MAX_PAGE_SIZE: Final[int] = 100


class SortDirection(StrEnum):
    ASC = "asc"
    DESC = "desc"


@dataclass(frozen=True, slots=True)
class Sort:
    field: str
    direction: SortDirection = SortDirection.ASC

    @classmethod
    def parse(cls, raw: str) -> Self:
        """Parse `field` (ascending) or `-field` (descending)."""
        name = raw.strip()
        direction = SortDirection.ASC
        if name.startswith("-"):
            name, direction = name[1:], SortDirection.DESC
        if not name:
            raise DomainValidationError(
                "Sort field cannot be empty.",
                code="invalid_sort_field",
                details={"sort": raw},
            )
        return cls(field=name, direction=direction)


@dataclass(frozen=True, slots=True)
class PageParams:
    page: int = 1
    size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            raise DomainValidationError(
                "Page must be greater than or equal to 1.",
                code="invalid_page",
                details={"page": self.page},
            )
        if not 1 <= self.size <= MAX_PAGE_SIZE:
            raise DomainValidationError(
                f"Page size must be between 1 and {MAX_PAGE_SIZE}.",
                code="invalid_page_size",
                details={"size": self.size},
            )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: Sequence[T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        return ceil(self.total / self.size) if self.size > 0 else 0

    def map[U](self, transform: Callable[[T], U]) -> "Page[U]":
        return Page(
            items=[transform(item) for item in self.items],
            total=self.total,
            page=self.page,
            size=self.size,
        )
```

`src/core/application/unit_of_work.py` :

```python
"""Unit of work contract."""

from typing import Protocol


class UnitOfWork(Protocol):
    """Atomic business transaction shared by every repository of a request."""

    async def commit(self) -> None:
        """
        Publish pending domain events, then persist every change atomically.

        :raises ConflictError: when a database constraint is violated.
        """
        ...

    async def rollback(self) -> None:
        """Discard every pending change."""
        ...
```

`src/core/application/event_bus.py` :

```python
"""Domain event publication contracts."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from core.domain.events import DomainEvent


class EventHandler[TEvent: DomainEvent](Protocol):
    """
    Reacts to one event type inside the unit of work that published it.

    Handlers share the publisher's transaction and must never commit.
    """

    async def handle(self, event: TEvent) -> None: ...


class EventBus(Protocol):
    async def publish(self, event: DomainEvent) -> None: ...


@dataclass(frozen=True, slots=True)
class EventHandlerRegistry:
    """Handler types to run for each event type, in order (exact type match)."""

    handlers: Mapping[type[DomainEvent], Sequence[type[EventHandler[Any]]]] = field(
        default_factory=dict
    )

    def handlers_for(self, event: DomainEvent) -> Sequence[type[EventHandler[Any]]]:
        return self.handlers.get(type(event), ())
```

- [ ] **Step 4: Vérifier le succès**

Run: `uv run pytest tests/unit/core -v`
Expected: tout passe.

- [ ] **Step 5: Lint et commit**

```bash
make format && make lint
git add src/core tests/unit/core
git commit -m "feat(core): add pagination primitives and application ports" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Tracker d'agrégats et bus d'événements in-process

**Files:**
- Create: `src/core/infrastructure/db/__init__.py` (vide), `src/core/infrastructure/db/tracker.py`, `src/core/infrastructure/events/__init__.py` (vide), `src/core/infrastructure/events/in_process_bus.py`
- Test: `tests/unit/core/test_tracker.py`, `tests/unit/core/test_in_process_bus.py`

**Interfaces:**
- Consumes: `AggregateRoot`, `DomainEvent` (Task 3) ; `EventBus`, `EventHandlerRegistry` (Task 4).
- Produces:
  - `core.infrastructure.db.tracker.AggregateTracker` : `track(aggregate: AggregateRoot[Any, Any]) -> None` (idempotent par identité d'objet), `pull_events() -> list[DomainEvent]` (ordre de suivi).
  - `core.infrastructure.events.in_process_bus.InProcessEventBus(container: AsyncContainer, registry: EventHandlerRegistry)` implémente `EventBus` : résout chaque handler dans le conteneur Dishka courant et l'attend séquentiellement.

- [ ] **Step 1: Écrire les tests qui échouent**

`tests/unit/core/test_tracker.py` :

```python
"""Aggregate tracker used by repositories and the unit of work."""

from core.infrastructure.db.tracker import AggregateTracker
from tests.unit.core.samples import SampleRenamed, make_sample


def test_pull_events_collects_events_of_tracked_aggregates_once() -> None:
    first, second = make_sample("a"), make_sample("b")
    first.rename("a2")
    second.rename("b2")
    tracker = AggregateTracker()

    tracker.track(first)
    tracker.track(second)
    tracker.track(first)
    events = tracker.pull_events()

    labels = [event.label for event in events if isinstance(event, SampleRenamed)]
    assert labels == ["a2", "b2"]
    assert len(events) == 2
    assert tracker.pull_events() == []


def test_untracked_aggregates_are_ignored() -> None:
    aggregate = make_sample()
    aggregate.rename("changed")

    assert AggregateTracker().pull_events() == []
```

`tests/unit/core/test_in_process_bus.py` :

```python
"""In-process event bus resolving handlers from the Dishka request container."""

from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
from dishka import (
    AsyncContainer,
    Provider,
    Scope,
    make_async_container,
    provide,
    provide_all,
)

from core.application.event_bus import EventBus, EventHandlerRegistry
from core.domain.events import DomainEvent
from core.infrastructure.events.in_process_bus import InProcessEventBus
from tests.unit.core.samples import SampleRenamed


@dataclass(frozen=True, slots=True, kw_only=True)
class UnhandledEvent(DomainEvent):
    """Event without any registered handler."""


class Journal:
    def __init__(self) -> None:
        self.entries: list[str] = []


class FirstHandler:
    def __init__(self, journal: Journal) -> None:
        self._journal = journal

    async def handle(self, event: SampleRenamed) -> None:
        self._journal.entries.append(f"first:{event.label}")


class SecondHandler:
    def __init__(self, journal: Journal) -> None:
        self._journal = journal

    async def handle(self, event: SampleRenamed) -> None:
        self._journal.entries.append(f"second:{event.label}")


class BusTestProvider(Provider):
    scope = Scope.REQUEST

    journal = provide(Journal)
    handlers = provide_all(FirstHandler, SecondHandler)
    event_bus = provide(InProcessEventBus, provides=EventBus)

    @provide(scope=Scope.APP)
    def registry(self) -> EventHandlerRegistry:
        return EventHandlerRegistry(
            handlers={SampleRenamed: (FirstHandler, SecondHandler)}
        )


@pytest.fixture
async def scope() -> AsyncIterator[AsyncContainer]:
    container = make_async_container(BusTestProvider())
    async with container() as request_container:
        yield request_container
    await container.close()


async def test_publish_awaits_registered_handlers_in_order(
    scope: AsyncContainer,
) -> None:
    bus = await scope.get(EventBus)

    await bus.publish(SampleRenamed(label="x"))

    journal = await scope.get(Journal)
    assert journal.entries == ["first:x", "second:x"]


async def test_publish_without_handlers_does_nothing(scope: AsyncContainer) -> None:
    bus = await scope.get(EventBus)

    await bus.publish(UnhandledEvent())

    journal = await scope.get(Journal)
    assert journal.entries == []
```

- [ ] **Step 2: Vérifier l'échec**

Run: `uv run pytest tests/unit/core/test_tracker.py tests/unit/core/test_in_process_bus.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Implémenter**

`src/core/infrastructure/db/tracker.py` :

```python
"""Request-scoped registry of the aggregates handled by repositories."""

from typing import Any

from core.domain.aggregate_root import AggregateRoot
from core.domain.events import DomainEvent


class AggregateTracker:
    """Remember the aggregates touched during a request to publish their events."""

    def __init__(self) -> None:
        self._aggregates: dict[int, AggregateRoot[Any, Any]] = {}

    def track(self, aggregate: AggregateRoot[Any, Any]) -> None:
        self._aggregates.setdefault(id(aggregate), aggregate)

    def pull_events(self) -> list[DomainEvent]:
        """Return the pending events of every tracked aggregate, in tracking order."""
        return [
            event
            for aggregate in self._aggregates.values()
            for event in aggregate.pull_events()
        ]
```

`src/core/infrastructure/events/in_process_bus.py` :

```python
"""Synchronous in-process event bus backed by the Dishka request container."""

import logging

from dishka import AsyncContainer

from core.application.event_bus import EventBus, EventHandlerRegistry
from core.domain.events import DomainEvent

log = logging.getLogger(__name__)


class InProcessEventBus(EventBus):
    """Resolve each registered handler from the current scope and await it in order."""

    def __init__(self, container: AsyncContainer, registry: EventHandlerRegistry) -> None:
        self._container = container
        self._registry = registry

    async def publish(self, event: DomainEvent) -> None:
        for handler_type in self._registry.handlers_for(event):
            handler = await self._container.get(handler_type)
            log.debug(
                "Dispatching %s to %s", type(event).__name__, handler_type.__name__
            )
            await handler.handle(event)
```

- [ ] **Step 4: Vérifier le succès**

Run: `uv run pytest tests/unit/core -v`
Expected: tout passe.

- [ ] **Step 5: Lint et commit**

```bash
make format && make lint
git add src/core/infrastructure tests/unit/core
git commit -m "feat(core): add aggregate tracker and in-process event bus" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Mapping des erreurs d'intégrité et UnitOfWork SQLAlchemy

**Files:**
- Create: `src/core/infrastructure/db/errors.py`, `src/core/infrastructure/db/unit_of_work.py`
- Test: `tests/unit/core/test_unit_of_work.py`

**Interfaces:**
- Consumes: `ConflictError` (Task 3), `UnitOfWork`, `EventBus` (Task 4), `AggregateTracker` (Task 5).
- Produces:
  - `core.infrastructure.db.errors` : `UNIQUE_VIOLATION = "23505"`, `FOREIGN_KEY_VIOLATION = "23503"`, `map_integrity_error(error: IntegrityError) -> ConflictError | None` (codes `unique_violation` / `foreign_key_violation`, `details = {"constraint": <nom>}` si connu).
  - `core.infrastructure.db.unit_of_work` : `MAX_EVENT_ROUNDS = 10`, `EventDispatchLoopError(RuntimeError)`, `SqlaUnitOfWork(session: AsyncSession, tracker: AggregateTracker, event_bus: EventBus)` implémente `UnitOfWork`. `commit()` : pour chaque tour (≤ 10) `flush` → `tracker.pull_events()` → publication ; puis `commit`. Toute exception → `rollback` puis propagation (`IntegrityError` connue traduite en `ConflictError`).

- [ ] **Step 1: Écrire les tests qui échouent**

`tests/unit/core/test_unit_of_work.py` :

```python
"""SQLAlchemy unit of work, with the session replaced by a recording fake."""

from collections.abc import Callable
from typing import cast

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.errors import ConflictError
from core.domain.events import DomainEvent
from core.infrastructure.db.errors import map_integrity_error
from core.infrastructure.db.tracker import AggregateTracker
from core.infrastructure.db.unit_of_work import (
    MAX_EVENT_ROUNDS,
    EventDispatchLoopError,
    SqlaUnitOfWork,
)
from tests.unit.core.samples import make_sample


class FakeDiagnostic:
    def __init__(self, constraint_name: str | None) -> None:
        self.constraint_name = constraint_name


class FakeDriverError(Exception):
    """Mimics psycopg errors, which expose `sqlstate` and `diag.constraint_name`."""

    def __init__(self, sqlstate: str, constraint_name: str | None = None) -> None:
        super().__init__(f"driver error {sqlstate}")
        self.sqlstate = sqlstate
        self.diag = FakeDiagnostic(constraint_name)


def integrity_error(sqlstate: str, constraint_name: str | None = None) -> IntegrityError:
    return IntegrityError("INSERT ...", {}, FakeDriverError(sqlstate, constraint_name))


class FakeSession:
    def __init__(self, commit_error: Exception | None = None) -> None:
        self.calls: list[str] = []
        self._commit_error = commit_error

    async def flush(self) -> None:
        self.calls.append("flush")

    async def commit(self) -> None:
        self.calls.append("commit")
        if self._commit_error is not None:
            raise self._commit_error

    async def rollback(self) -> None:
        self.calls.append("rollback")


class RecordingBus:
    def __init__(
        self,
        session: FakeSession,
        on_publish: Callable[[DomainEvent], None] | None = None,
    ) -> None:
        self.published: list[DomainEvent] = []
        self._session = session
        self._on_publish = on_publish

    async def publish(self, event: DomainEvent) -> None:
        self._session.calls.append(f"publish:{type(event).__name__}")
        self.published.append(event)
        if self._on_publish is not None:
            self._on_publish(event)


def make_uow(
    session: FakeSession, tracker: AggregateTracker, bus: RecordingBus
) -> SqlaUnitOfWork:
    return SqlaUnitOfWork(
        session=cast(AsyncSession, session), tracker=tracker, event_bus=bus
    )


async def test_commit_without_events_flushes_then_commits() -> None:
    session = FakeSession()

    await make_uow(session, AggregateTracker(), RecordingBus(session)).commit()

    assert session.calls == ["flush", "commit"]


async def test_commit_publishes_recorded_events_before_committing() -> None:
    session = FakeSession()
    tracker = AggregateTracker()
    aggregate = make_sample()
    aggregate.rename("second")
    tracker.track(aggregate)

    await make_uow(session, tracker, RecordingBus(session)).commit()

    assert session.calls == ["flush", "publish:SampleRenamed", "flush", "commit"]


async def test_events_recorded_by_handlers_are_published_in_a_next_round() -> None:
    session = FakeSession()
    tracker = AggregateTracker()
    first, second = make_sample("a"), make_sample("b")
    first.rename("a2")
    tracker.track(first)
    tracker.track(second)

    def rename_second_once(_event: DomainEvent) -> None:
        if second.props.label == "b":
            second.rename("b2")

    bus = RecordingBus(session, on_publish=rename_second_once)
    await make_uow(session, tracker, bus).commit()

    assert session.calls == [
        "flush",
        "publish:SampleRenamed",
        "flush",
        "publish:SampleRenamed",
        "flush",
        "commit",
    ]


async def test_dispatch_that_never_converges_is_aborted_and_rolled_back() -> None:
    session = FakeSession()
    tracker = AggregateTracker()
    aggregate = make_sample()
    aggregate.rename("again")
    tracker.track(aggregate)
    bus = RecordingBus(session, on_publish=lambda _event: aggregate.rename("again"))

    with pytest.raises(EventDispatchLoopError):
        await make_uow(session, tracker, bus).commit()

    assert len(bus.published) == MAX_EVENT_ROUNDS
    assert "commit" not in session.calls
    assert session.calls[-1] == "rollback"


async def test_handler_failure_rolls_back_and_propagates() -> None:
    session = FakeSession()
    tracker = AggregateTracker()
    aggregate = make_sample()
    aggregate.rename("x")
    tracker.track(aggregate)

    def explode(_event: DomainEvent) -> None:
        raise RuntimeError("handler failed")

    bus = RecordingBus(session, on_publish=explode)
    with pytest.raises(RuntimeError, match="handler failed"):
        await make_uow(session, tracker, bus).commit()

    assert session.calls == ["flush", "publish:SampleRenamed", "rollback"]


async def test_unique_violation_becomes_a_conflict_error() -> None:
    session = FakeSession(commit_error=integrity_error("23505", "uq_samples_label"))

    with pytest.raises(ConflictError) as exc_info:
        await make_uow(session, AggregateTracker(), RecordingBus(session)).commit()

    assert exc_info.value.code == "unique_violation"
    assert exc_info.value.details == {"constraint": "uq_samples_label"}
    assert session.calls == ["flush", "commit", "rollback"]


async def test_unknown_integrity_error_is_reraised_after_rollback() -> None:
    session = FakeSession(commit_error=integrity_error("23514"))

    with pytest.raises(IntegrityError):
        await make_uow(session, AggregateTracker(), RecordingBus(session)).commit()

    assert session.calls[-1] == "rollback"


async def test_rollback_delegates_to_the_session() -> None:
    session = FakeSession()

    await make_uow(session, AggregateTracker(), RecordingBus(session)).rollback()

    assert session.calls == ["rollback"]


@pytest.mark.parametrize(
    ("sqlstate", "code"),
    [("23505", "unique_violation"), ("23503", "foreign_key_violation")],
)
def test_map_integrity_error_known_sqlstates(sqlstate: str, code: str) -> None:
    error = map_integrity_error(integrity_error(sqlstate, "some_constraint"))

    assert isinstance(error, ConflictError)
    assert error.code == code
    assert error.details == {"constraint": "some_constraint"}


def test_map_integrity_error_without_constraint_name() -> None:
    error = map_integrity_error(integrity_error("23505"))

    assert error is not None
    assert error.details == {}


def test_map_integrity_error_unknown_sqlstate() -> None:
    assert map_integrity_error(integrity_error("23514")) is None
```

- [ ] **Step 2: Vérifier l'échec**

Run: `uv run pytest tests/unit/core/test_unit_of_work.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'core.infrastructure.db.errors'`).

- [ ] **Step 3: Implémenter**

`src/core/infrastructure/db/errors.py` :

```python
"""Translate database integrity errors into domain errors."""

from typing import Any, Final

from sqlalchemy.exc import IntegrityError

from core.domain.errors import ConflictError

UNIQUE_VIOLATION: Final[str] = "23505"
FOREIGN_KEY_VIOLATION: Final[str] = "23503"


def map_integrity_error(error: IntegrityError) -> ConflictError | None:
    """Return the domain error matching the driver SQLSTATE, or `None` if unknown."""
    sqlstate = getattr(error.orig, "sqlstate", None)
    diagnostic = getattr(error.orig, "diag", None)
    constraint = getattr(diagnostic, "constraint_name", None)
    details: dict[str, Any] = {"constraint": constraint} if constraint else {}
    if sqlstate == UNIQUE_VIOLATION:
        return ConflictError(
            "The resource already exists.",
            code="unique_violation",
            details=details,
        )
    if sqlstate == FOREIGN_KEY_VIOLATION:
        return ConflictError(
            "The resource is linked to another resource.",
            code="foreign_key_violation",
            details=details,
        )
    return None
```

`src/core/infrastructure/db/unit_of_work.py` :

```python
"""SQLAlchemy implementation of the unit of work."""

import logging
from typing import Final

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.application.event_bus import EventBus
from core.application.unit_of_work import UnitOfWork
from core.infrastructure.db.errors import map_integrity_error
from core.infrastructure.db.tracker import AggregateTracker

log = logging.getLogger(__name__)

MAX_EVENT_ROUNDS: Final[int] = 10


class EventDispatchLoopError(RuntimeError):
    """Handlers kept recording events after `MAX_EVENT_ROUNDS` dispatch rounds."""


class SqlaUnitOfWork(UnitOfWork):
    """
    Commit a business transaction atomically.

    Each dispatch round flushes pending changes, then publishes the events recorded
    by tracked aggregates. Handlers run in the same session and may record new
    events, published in the next round. The session is committed once no event is
    left; any failure rolls the whole transaction back.
    """

    def __init__(
        self, session: AsyncSession, tracker: AggregateTracker, event_bus: EventBus
    ) -> None:
        self._session = session
        self._tracker = tracker
        self._event_bus = event_bus

    async def commit(self) -> None:
        try:
            await self._dispatch_events()
            await self._session.commit()
        except IntegrityError as err:
            await self._session.rollback()
            conflict = map_integrity_error(err)
            if conflict is None:
                raise
            raise conflict from err
        except Exception:
            await self._session.rollback()
            raise
        log.debug("Transaction committed.")

    async def rollback(self) -> None:
        await self._session.rollback()

    async def _dispatch_events(self) -> None:
        for _ in range(MAX_EVENT_ROUNDS):
            await self._session.flush()
            events = self._tracker.pull_events()
            if not events:
                return
            for event in events:
                await self._event_bus.publish(event)
        raise EventDispatchLoopError(
            f"Events were still produced after {MAX_EVENT_ROUNDS} dispatch rounds."
        )
```

- [ ] **Step 4: Vérifier le succès**

Run: `uv run pytest tests/unit/core/test_unit_of_work.py -v`
Expected: 12 passed.

- [ ] **Step 5: Lint et commit**

```bash
make format && make lint
git add src/core/infrastructure/db tests/unit/core
git commit -m "feat(core): add SQLAlchemy unit of work with in-transaction event dispatch" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Base ORM, mixins, helpers de requête et `SqlaRepository`

**Files:**
- Create: `src/core/infrastructure/db/base.py`, `src/core/infrastructure/db/mixins.py`, `src/core/infrastructure/db/mapper.py`, `src/core/infrastructure/db/query.py`, `src/core/infrastructure/db/repository.py`
- Test: `tests/unit/core/test_query.py`

**Interfaces:**
- Consumes: `AggregateRoot`, `EntityId`, `DomainValidationError` (Task 3) ; `Page`, `PageParams`, `Sort`, `SortDirection` (Task 4) ; `AggregateTracker` (Task 5).
- Produces:
  - `core.infrastructure.db.base` : `NAMING_CONVENTION`, `Base(DeclarativeBase)` avec `metadata = MetaData(naming_convention=NAMING_CONVENTION)`.
  - `core.infrastructure.db.mixins` : `UUIDPrimaryKeyMixin` (`id: Mapped[UUID]`), `TimestampMixin` (`created_at`, `updated_at`: `Mapped[datetime]`, timezone-aware, non nuls, sans défaut serveur).
  - `core.infrastructure.db.mapper.EntityMapper[TEntity, TModel]` (Protocol) : `to_model(entity) -> TModel`, `to_entity(model) -> TEntity`.
  - `core.infrastructure.db.query` : `escape_like(value: str) -> str` ; `build_order_by(model, sort, *, allowed) -> list[ColumnElement[Any]]` (ajoute la clé primaire ASC) ; `build_filters(model, filters, *, allowed) -> list[ColumnElement[bool]]` ; `build_search(model, search, *, fields) -> list[ColumnElement[bool]]`. Champ hors liste blanche → `DomainValidationError` (`invalid_sort_field` / `invalid_filter_field`, `details = {"field", "allowed"}`).
  - `core.infrastructure.db.repository.SqlaRepository[TEntity: AggregateRoot, TModel: Base]` : `__init__(*, session, tracker, model, mapper)` ; attributs de classe `sortable_fields: frozenset[str]` (défaut `{"created_at", "updated_at"}`), `filterable_fields: frozenset[str]` (défaut vide), `searchable_fields: tuple[str, ...]` (défaut vide) ; méthodes `add(entity)`, `save(entity)`, `delete(entity)`, `get_by_id(entity_id: EntityId) -> TEntity | None`, `list_page(params, *, sort=None, filters=None, search=None) -> Page[TEntity]` (tri par défaut `-created_at`). Attributs protégés utilisables par les sous-classes : `_session`, `_tracker`, `_model`, `_mapper`.

- [ ] **Step 1: Écrire les tests qui échouent**

`tests/unit/core/test_query.py` :

```python
"""Whitelisted sort / filter / search helpers, compiled to SQL without a database."""

import pytest
from sqlalchemy import Select, String, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from core.domain.errors import DomainValidationError
from core.domain.pagination import Sort, SortDirection
from core.infrastructure.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from core.infrastructure.db.query import (
    build_filters,
    build_order_by,
    build_search,
    escape_like,
)


class QueryTestBase(DeclarativeBase):
    """Separate metadata: this table never reaches the application schema."""


class ArticleModel(UUIDPrimaryKeyMixin, TimestampMixin, QueryTestBase):
    __tablename__ = "articles"

    title: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20))


def to_sql(statement: Select[tuple[ArticleModel]]) -> str:
    return str(statement.compile(dialect=postgresql.dialect()))


def test_escape_like_escapes_wildcards_and_backslashes() -> None:
    assert escape_like("50%_off\\now") == "50\\%\\_off\\\\now"


def test_order_by_applies_direction_and_primary_key_tiebreaker() -> None:
    order_by = build_order_by(
        ArticleModel, Sort("title", SortDirection.DESC), allowed={"title"}
    )

    sql = to_sql(select(ArticleModel).order_by(*order_by))

    assert "ORDER BY articles.title DESC, articles.id ASC" in sql


@pytest.mark.parametrize("field", ["status", "metadata", "__table__"])
def test_order_by_rejects_fields_outside_the_whitelist(field: str) -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        build_order_by(ArticleModel, Sort(field), allowed={"title", "created_at"})

    assert exc_info.value.code == "invalid_sort_field"
    assert exc_info.value.details == {
        "field": field,
        "allowed": ["created_at", "title"],
    }


def test_filters_build_equality_conditions() -> None:
    conditions = build_filters(ArticleModel, {"status": "active"}, allowed={"status"})

    sql = to_sql(select(ArticleModel).where(*conditions))

    assert "WHERE articles.status = %(status_1)s" in sql


def test_filters_reject_fields_outside_the_whitelist() -> None:
    with pytest.raises(DomainValidationError) as exc_info:
        build_filters(ArticleModel, {"title": "x"}, allowed={"status"})

    assert exc_info.value.code == "invalid_filter_field"


def test_search_matches_any_field_with_an_escaped_pattern() -> None:
    conditions = build_search(ArticleModel, "50%", fields=("title", "status"))
    statement = select(ArticleModel).where(*conditions)

    sql = to_sql(statement)

    assert "articles.title ILIKE %(title_1)s ESCAPE" in sql
    assert " OR articles.status ILIKE %(status_1)s ESCAPE" in sql
    assert statement.compile().params["title_1"] == "%50\\%%"


@pytest.mark.parametrize("search", [None, ""])
def test_search_without_term_adds_no_condition(search: str | None) -> None:
    assert build_search(ArticleModel, search, fields=("title",)) == []


def test_search_without_searchable_fields_adds_no_condition() -> None:
    assert build_search(ArticleModel, "term", fields=()) == []
```

- [ ] **Step 2: Vérifier l'échec**

Run: `uv run pytest tests/unit/core/test_query.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'core.infrastructure.db.mixins'`).

- [ ] **Step 3: Implémenter**

`src/core/infrastructure/db/base.py` :

```python
"""Declarative base of every ORM model of the application."""

from typing import Final

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION: Final[dict[str, str]] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Constraint names are deterministic, which keeps Alembic migrations stable."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
```

`src/core/infrastructure/db/mixins.py` :

```python
"""Reusable ORM columns."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """UUID primary key; the value is generated by the domain (UUID v7)."""

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)


class TimestampMixin:
    """Timestamps owned by the domain entity (`created_at_`, `updated_at_`)."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
```

`src/core/infrastructure/db/mapper.py` :

```python
"""Mapping contract between domain entities and ORM models."""

from typing import Protocol


class EntityMapper[TEntity, TModel](Protocol):
    def to_model(self, entity: TEntity) -> TModel: ...

    def to_entity(self, model: TModel) -> TEntity: ...
```

`src/core/infrastructure/db/query.py` :

```python
"""Whitelisted sorting, filtering and searching for SQLAlchemy selects."""

from collections.abc import Iterable, Mapping
from typing import Any

from sqlalchemy import ColumnElement, inspect, or_

from core.domain.errors import DomainValidationError
from core.domain.pagination import Sort, SortDirection

LIKE_ESCAPE_CHARACTER = "\\"


def escape_like(value: str) -> str:
    """Escape LIKE wildcards so that user input is matched literally."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def build_order_by(
    model: type[Any], sort: Sort, *, allowed: Iterable[str]
) -> list[ColumnElement[Any]]:
    _ensure_allowed(sort.field, allowed, purpose="sort")
    column = _column(model, sort.field)
    ordered = column.desc() if sort.direction is SortDirection.DESC else column.asc()
    primary_key = inspect(model).primary_key[0]
    return [ordered, primary_key.asc()]


def build_filters(
    model: type[Any], filters: Mapping[str, object], *, allowed: Iterable[str]
) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []
    for name, value in filters.items():
        _ensure_allowed(name, allowed, purpose="filter")
        conditions.append(_column(model, name) == value)
    return conditions


def build_search(
    model: type[Any], search: str | None, *, fields: Iterable[str]
) -> list[ColumnElement[bool]]:
    names = list(fields)
    if not search or not names:
        return []
    pattern = f"%{escape_like(search)}%"
    return [
        or_(
            *(
                _column(model, name).ilike(pattern, escape=LIKE_ESCAPE_CHARACTER)
                for name in names
            )
        )
    ]


def _column(model: type[Any], name: str) -> ColumnElement[Any]:
    return inspect(model).columns[name]


def _ensure_allowed(name: str, allowed: Iterable[str], *, purpose: str) -> None:
    allowed_names = sorted(allowed)
    if name not in allowed_names:
        raise DomainValidationError(
            f"Cannot {purpose} by '{name}'.",
            code=f"invalid_{purpose}_field",
            details={"field": name, "allowed": allowed_names},
        )
```

`src/core/infrastructure/db/repository.py` :

```python
"""Generic SQLAlchemy repository for aggregate roots."""

from collections.abc import Mapping
from typing import Any, ClassVar

from sqlalchemy import delete, func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.aggregate_root import AggregateRoot
from core.domain.identifier import EntityId
from core.domain.pagination import Page, PageParams, Sort, SortDirection
from core.infrastructure.db.base import Base
from core.infrastructure.db.mapper import EntityMapper
from core.infrastructure.db.query import build_filters, build_order_by, build_search
from core.infrastructure.db.tracker import AggregateTracker

DEFAULT_SORT = Sort("created_at", SortDirection.DESC)


class SqlaRepository[TEntity: AggregateRoot[Any, Any], TModel: Base]:
    """
    Persistence and paginated listing of one aggregate type.

    Subclasses declare the columns clients may sort, filter and search on. Every
    aggregate added, saved, deleted or loaded by id is tracked so that the unit of
    work publishes its domain events.
    """

    sortable_fields: ClassVar[frozenset[str]] = frozenset({"created_at", "updated_at"})
    filterable_fields: ClassVar[frozenset[str]] = frozenset()
    searchable_fields: ClassVar[tuple[str, ...]] = ()

    def __init__(
        self,
        *,
        session: AsyncSession,
        tracker: AggregateTracker,
        model: type[TModel],
        mapper: EntityMapper[TEntity, TModel],
    ) -> None:
        self._session = session
        self._tracker = tracker
        self._model = model
        self._mapper = mapper

    async def add(self, entity: TEntity) -> None:
        self._session.add(self._mapper.to_model(entity))
        self._tracker.track(entity)

    async def save(self, entity: TEntity) -> None:
        await self._session.merge(self._mapper.to_model(entity))
        self._tracker.track(entity)

    async def delete(self, entity: TEntity) -> None:
        primary_key = inspect(self._model).primary_key[0]
        statement = delete(self._model).where(primary_key == entity.id_.value)
        await self._session.execute(statement)
        self._tracker.track(entity)

    async def get_by_id(self, entity_id: EntityId) -> TEntity | None:
        model = await self._session.get(self._model, entity_id.value)
        if model is None:
            return None
        entity = self._mapper.to_entity(model)
        self._tracker.track(entity)
        return entity

    async def list_page(
        self,
        params: PageParams,
        *,
        sort: Sort | None = None,
        filters: Mapping[str, object] | None = None,
        search: str | None = None,
    ) -> Page[TEntity]:
        conditions = [
            *build_filters(self._model, filters or {}, allowed=self.filterable_fields),
            *build_search(self._model, search, fields=self.searchable_fields),
        ]
        order_by = build_order_by(
            self._model, sort or DEFAULT_SORT, allowed=self.sortable_fields
        )
        count = select(func.count()).select_from(self._model).where(*conditions)
        total = await self._session.scalar(count) or 0
        statement = (
            select(self._model)
            .where(*conditions)
            .order_by(*order_by)
            .offset(params.offset)
            .limit(params.size)
        )
        models = (await self._session.scalars(statement)).all()
        return Page(
            items=[self._mapper.to_entity(model) for model in models],
            total=total,
            page=params.page,
            size=params.size,
        )
```

`SqlaRepository` n'a pas de test unitaire : il est couvert par les tests d'intégration des repositories (Tasks 12 et 16).

- [ ] **Step 4: Vérifier le succès**

Run: `uv run pytest tests/unit/core -v`
Expected: tout passe.

- [ ] **Step 5: Lint et commit**

```bash
make format && make lint
git add src/core/infrastructure/db tests/unit/core
git commit -m "feat(core): add ORM base, whitelisted query helpers and generic repository" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Couche HTTP, providers Dishka et factory d'application

**Files:**
- Create: `src/core/infrastructure/db/provider.py`, `src/core/infrastructure/provider.py`, `src/core/presentation/__init__.py` (vide), `src/core/presentation/http/__init__.py` (vide), `src/core/presentation/http/errors.py`, `src/core/presentation/http/pagination.py`, `src/core/presentation/http/health.py`, `src/app/main.py`, `src/app/lifespan.py`, `src/app/routers.py`, `src/app/providers.py`, `src/app/event_handlers.py`, `scripts/dishka/plot_dependencies_data.py`
- Modify: `pyproject.toml` (`[tool.mypy] files`)
- Test: `tests/unit/app/__init__.py` (vide), `tests/unit/app/test_app.py`

**Interfaces:**
- Consumes: settings/logs (Task 2), erreurs et pagination (Tasks 3-4), `InProcessEventBus`, `AggregateTracker` (Task 5), `SqlaUnitOfWork` (Task 6).
- Produces:
  - `core.infrastructure.db.provider.DatabaseProvider` : `AsyncEngine` (APP, disposé à la fermeture), `async_sessionmaker[AsyncSession]` (APP), `AsyncSession` (REQUEST), `AggregateTracker` (REQUEST), `UnitOfWork` → `SqlaUnitOfWork` (REQUEST).
  - `core.infrastructure.provider` : `SettingsProvider` (`Settings` depuis le contexte, `DatabaseSettings`), `EventsProvider` (`EventBus` → `InProcessEventBus`, REQUEST), `core_providers() -> tuple[Provider, ...]`.
  - `core.presentation.http.errors` : `PROBLEM_JSON_MEDIA_TYPE`, `ProblemDetails`, `error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]`, `status_code_for(error: DomainError) -> int`, `problem_response(...)`, `register_error_handlers(app: FastAPI) -> None`.
  - `core.presentation.http.pagination` : `PageResponse[T](items, total, page, size, pages)`, `to_page_response(page: Page[T], item_type: type[R]) -> PageResponse[R]`.
  - `core.presentation.http.health.create_health_router() -> APIRouter` (`GET /health`, `GET /health/ready`).
  - `app.main.create_app(settings: Settings | None = None, *providers: Provider) -> FastAPI` : les `providers` passés sont ajoutés après ceux par défaut et les surchargent.
  - `app.routers` : `create_api_v1_router() -> APIRouter` (préfixe `/api/v1`, vide pour l'instant), `create_root_router(*, docs_enabled: bool) -> APIRouter`.
  - `app.providers.get_providers() -> tuple[Provider, ...]`.
  - `app.event_handlers.EventHandlersProvider` : fournit `EventHandlerRegistry` (APP), vide pour l'instant.

- [ ] **Step 1: Écrire les tests qui échouent**

`tests/unit/app/test_app.py` :

```python
"""Application factory, error rendering and health probes (no database needed)."""

from collections.abc import AsyncIterator
from http import HTTPStatus

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from app.main import create_app
from core.domain.errors import (
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
    DomainValidationError,
    NotFoundError,
)
from core.infrastructure.settings import (
    AppSettings,
    CorsSettings,
    DatabaseSettings,
    Settings,
)

UNREACHABLE_DATABASE = DatabaseSettings(
    host="127.0.0.1", port=1, password=SecretStr("unused")
)


def make_settings(
    *, docs_enabled: bool = True, allow_origins: list[str] | None = None
) -> Settings:
    return Settings(
        app=AppSettings(docs_enabled=docs_enabled),
        database=UNREACHABLE_DATABASE,
        cors=CorsSettings(allow_origins=allow_origins or []),
        _env_file=None,
    )


@pytest.fixture
async def app() -> AsyncIterator[FastAPI]:
    application = create_app(make_settings())
    yield application
    await application.state.dishka_container.close()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


async def test_liveness(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}


async def test_readiness_reports_an_unreachable_database(client: AsyncClient) -> None:
    response = await client.get("/health/ready")

    assert response.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert response.json() == {"status": "unavailable"}


async def test_root_redirects_to_docs(client: AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == HTTPStatus.TEMPORARY_REDIRECT
    assert response.headers["location"] == "/docs"


@pytest.mark.parametrize(
    ("error", "status_code"),
    [
        (NotFoundError("Missing.", code="thing_not_found"), HTTPStatus.NOT_FOUND),
        (ConflictError("Taken."), HTTPStatus.CONFLICT),
        (BusinessRuleViolationError("Not allowed."), HTTPStatus.CONFLICT),
        (DomainValidationError("Invalid."), HTTPStatus.UNPROCESSABLE_CONTENT),
        (DomainError("Bad request."), HTTPStatus.BAD_REQUEST),
    ],
)
async def test_domain_errors_are_problem_details(
    app: FastAPI, client: AsyncClient, error: DomainError, status_code: HTTPStatus
) -> None:
    async def raise_error() -> None:
        raise error

    app.add_api_route("/boom", raise_error)

    response = await client.get("/boom")

    assert response.status_code == status_code
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json() == {
        "type": "about:blank",
        "title": status_code.phrase,
        "status": status_code,
        "detail": error.message,
        "code": error.code,
    }


async def test_domain_error_details_are_included(
    app: FastAPI, client: AsyncClient
) -> None:
    async def raise_error() -> None:
        raise NotFoundError("Missing.", details={"id": "42"})

    app.add_api_route("/boom", raise_error)

    response = await client.get("/boom")

    assert response.json()["details"] == {"id": "42"}


async def test_unexpected_errors_return_a_generic_500(
    app: FastAPI, client: AsyncClient
) -> None:
    async def raise_error() -> None:
        raise RuntimeError("secret internals")

    app.add_api_route("/boom", raise_error)

    response = await client.get("/boom")

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert response.json() == {
        "type": "about:blank",
        "title": "Internal Server Error",
        "status": 500,
        "code": "internal_error",
    }
    assert "secret internals" not in response.text


async def test_request_validation_errors_are_problem_details(
    app: FastAPI, client: AsyncClient
) -> None:
    async def read_items(limit: int) -> dict[str, int]:
        return {"limit": limit}

    app.add_api_route("/items", read_items)

    response = await client.get("/items", params={"limit": "abc"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert response.headers["content-type"] == "application/problem+json"
    body = response.json()
    assert body["code"] == "request_validation_error"
    assert body["errors"][0]["loc"] == ["query", "limit"]


async def test_unknown_routes_are_problem_details(client: AsyncClient) -> None:
    response = await client.get("/does-not-exist")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["detail"] == "Not Found"


async def test_docs_can_be_disabled() -> None:
    application = create_app(make_settings(docs_enabled=False))
    transport = ASGITransport(app=application, raise_app_exceptions=False)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for path in ("/", "/docs", "/redoc", "/openapi.json"):
                response = await client.get(path)
                assert response.status_code == HTTPStatus.NOT_FOUND, path
    finally:
        await application.state.dishka_container.close()


async def test_cors_is_enabled_for_configured_origins() -> None:
    origin = "http://localhost:3000"
    application = create_app(make_settings(allow_origins=[origin]))
    transport = ASGITransport(app=application, raise_app_exceptions=False)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health", headers={"Origin": origin})
        assert response.headers["access-control-allow-origin"] == origin
    finally:
        await application.state.dishka_container.close()
```

- [ ] **Step 2: Vérifier l'échec**

Run: `uv run pytest tests/unit/app -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'app.main'`).

- [ ] **Step 3: Implémenter les providers core**

`src/core/infrastructure/db/provider.py` :

```python
"""Database dependencies: one engine for the app, one session per request."""

from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from core.application.unit_of_work import UnitOfWork
from core.infrastructure.db.tracker import AggregateTracker
from core.infrastructure.db.unit_of_work import SqlaUnitOfWork
from core.infrastructure.settings import DatabaseSettings

CONNECT_TIMEOUT_SECONDS = 5


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    async def engine(self, settings: DatabaseSettings) -> AsyncIterator[AsyncEngine]:
        engine = create_async_engine(
            settings.url,
            echo=settings.echo,
            echo_pool=settings.echo_pool,
            pool_size=settings.pool_size,
            max_overflow=settings.max_overflow,
            pool_pre_ping=True,
            connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
        )
        yield engine
        await engine.dispose()

    @provide(scope=Scope.APP)
    def session_factory(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

    @provide(scope=Scope.REQUEST)
    async def session(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    tracker = provide(AggregateTracker, scope=Scope.REQUEST)
    unit_of_work = provide(SqlaUnitOfWork, scope=Scope.REQUEST, provides=UnitOfWork)
```

`src/core/infrastructure/provider.py` :

```python
"""Dishka providers of the shared kernel."""

from dishka import Provider, Scope, from_context, provide

from core.application.event_bus import EventBus
from core.infrastructure.db.provider import DatabaseProvider
from core.infrastructure.events.in_process_bus import InProcessEventBus
from core.infrastructure.settings import DatabaseSettings, Settings


class SettingsProvider(Provider):
    scope = Scope.APP

    settings = from_context(provides=Settings, scope=Scope.APP)

    @provide
    def database_settings(self, settings: Settings) -> DatabaseSettings:
        return settings.database


class EventsProvider(Provider):
    event_bus = provide(InProcessEventBus, scope=Scope.REQUEST, provides=EventBus)


def core_providers() -> tuple[Provider, ...]:
    return (SettingsProvider(), DatabaseProvider(), EventsProvider())
```

- [ ] **Step 4: Implémenter la présentation HTTP du core**

`src/core/presentation/http/errors.py` :

```python
"""Render every error as RFC 9457 problem details (`application/problem+json`)."""

import logging
from collections.abc import Mapping
from http import HTTPStatus
from typing import Any, Final, cast

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.domain.errors import (
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
    DomainValidationError,
    NotFoundError,
)

log = logging.getLogger(__name__)

PROBLEM_JSON_MEDIA_TYPE: Final[str] = "application/problem+json"

STATUS_BY_ERROR_TYPE: Final[tuple[tuple[type[DomainError], int], ...]] = (
    (NotFoundError, HTTPStatus.NOT_FOUND),
    (ConflictError, HTTPStatus.CONFLICT),
    (BusinessRuleViolationError, HTTPStatus.CONFLICT),
    (DomainValidationError, HTTPStatus.UNPROCESSABLE_CONTENT),
)


class ProblemDetails(BaseModel):
    """RFC 9457 problem details, documented in OpenAPI for error responses."""

    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    code: str | None = None
    details: dict[str, Any] | None = None
    errors: list[dict[str, Any]] | None = None


def error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    """OpenAPI `responses` entries for the given error status codes."""
    return {
        code: {"model": ProblemDetails, "description": HTTPStatus(code).phrase}
        for code in status_codes
    }


def status_code_for(error: DomainError) -> int:
    for error_type, status_code in STATUS_BY_ERROR_TYPE:
        if isinstance(error, error_type):
            return status_code
    return HTTPStatus.BAD_REQUEST


def problem_response(
    *,
    status_code: int,
    detail: str | None = None,
    code: str | None = None,
    extra: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {
        "type": "about:blank",
        "title": HTTPStatus(status_code).phrase,
        "status": int(status_code),
    }
    if detail is not None:
        body["detail"] = detail
    if code is not None:
        body["code"] = code
    if extra:
        body.update(extra)
    return JSONResponse(
        content=jsonable_encoder(body),
        status_code=status_code,
        headers=headers,
        media_type=PROBLEM_JSON_MEDIA_TYPE,
    )


async def handle_domain_error(_request: Request, exc: Exception) -> JSONResponse:
    error = cast(DomainError, exc)
    return problem_response(
        status_code=status_code_for(error),
        detail=error.message,
        code=error.code,
        extra={"details": error.details} if error.details else None,
    )


async def handle_request_validation_error(
    _request: Request, exc: Exception
) -> JSONResponse:
    error = cast(RequestValidationError, exc)
    return problem_response(
        status_code=HTTPStatus.UNPROCESSABLE_CONTENT,
        detail="The request is invalid.",
        code="request_validation_error",
        extra={"errors": error.errors()},
    )


async def handle_http_exception(_request: Request, exc: Exception) -> JSONResponse:
    error = cast(StarletteHTTPException, exc)
    return problem_response(
        status_code=error.status_code, detail=str(error.detail), headers=error.headers
    )


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    log.error(
        "Unhandled error on %s %s", request.method, request.url.path, exc_info=exc
    )
    return problem_response(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR, code="internal_error"
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, handle_domain_error)
    app.add_exception_handler(RequestValidationError, handle_request_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(Exception, handle_unexpected_error)
```

`src/core/presentation/http/pagination.py` :

```python
"""Paginated HTTP responses."""

from pydantic import BaseModel

from core.domain.pagination import Page


class PageResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


def to_page_response[T, R: BaseModel](
    page: Page[T], item_type: type[R]
) -> PageResponse[R]:
    """Validate every item (usually a DTO) of a domain page into `item_type`."""
    return PageResponse(
        items=[item_type.model_validate(item, from_attributes=True) for item in page.items],
        total=page.total,
        page=page.page,
        size=page.size,
        pages=page.pages,
    )
```

`src/core/presentation/http/health.py` :

```python
"""Liveness and readiness probes."""

import logging
from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

log = logging.getLogger(__name__)


def create_health_router() -> APIRouter:
    router = APIRouter(tags=["Health"])

    @router.get("/health", summary="Liveness probe")
    async def liveness() -> dict[str, str]:
        return {"status": "ok"}

    @router.get(
        "/health/ready",
        summary="Readiness probe (checks the database)",
        responses={HTTPStatus.SERVICE_UNAVAILABLE: {"description": "Database down"}},
    )
    @inject
    async def readiness(engine: FromDishka[AsyncEngine]) -> JSONResponse:
        try:
            async with engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
        except SQLAlchemyError:
            log.warning("Readiness check failed: database unavailable", exc_info=True)
            return JSONResponse(
                {"status": "unavailable"}, status_code=HTTPStatus.SERVICE_UNAVAILABLE
            )
        return JSONResponse({"status": "ok"})

    return router
```

- [ ] **Step 5: Implémenter la racine de composition `app`**

`src/app/event_handlers.py` :

```python
"""Wiring of domain events to the handlers that react to them."""

from dishka import Provider, Scope, provide

from core.application.event_bus import EventHandlerRegistry


class EventHandlersProvider(Provider):
    """Register here every handler that must run when a domain event is published."""

    @provide(scope=Scope.APP)
    def registry(self) -> EventHandlerRegistry:
        return EventHandlerRegistry(handlers={})
```

`src/app/providers.py` :

```python
"""Every Dishka provider of the application."""

from dishka import Provider

from app.event_handlers import EventHandlersProvider
from core.infrastructure.provider import core_providers


def get_providers() -> tuple[Provider, ...]:
    return (*core_providers(), EventHandlersProvider())
```

`src/app/routers.py` :

```python
"""HTTP routing of the application."""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from core.presentation.http.health import create_health_router


def create_api_v1_router() -> APIRouter:
    return APIRouter(prefix="/api/v1")


def create_root_router(*, docs_enabled: bool) -> APIRouter:
    router = APIRouter()

    if docs_enabled:

        @router.get("/", include_in_schema=False)
        async def redirect_to_docs() -> RedirectResponse:
            return RedirectResponse(url="/docs")

    router.include_router(create_health_router())
    router.include_router(create_api_v1_router())
    return router
```

`src/app/lifespan.py` :

```python
"""Application lifespan."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Close the Dishka container, which disposes the database engine, on shutdown."""
    yield
    await app.state.dishka_container.close()
```

`src/app/main.py` :

```python
"""FastAPI application factory (`uvicorn app.main:create_app --factory`)."""

from dishka import Provider, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.lifespan import lifespan
from app.providers import get_providers
from app.routers import create_root_router
from core.infrastructure.logs import configure_logging
from core.infrastructure.settings import Settings
from core.presentation.http.errors import register_error_handlers


def create_app(settings: Settings | None = None, *providers: Provider) -> FastAPI:
    """
    Build the application.

    `providers` are registered after the default ones and therefore override them,
    which lets tests replace any dependency.
    """
    settings = settings or Settings()
    configure_logging(settings.log.level)
    docs_enabled = settings.app.docs_enabled

    app = FastAPI(
        title=settings.app.name,
        version=settings.app.version,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
        lifespan=lifespan,
    )
    if settings.cors.allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors.allow_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    register_error_handlers(app)
    app.include_router(create_root_router(docs_enabled=docs_enabled))

    container = make_async_container(
        *get_providers(), *providers, context={Settings: settings}
    )
    setup_dishka(container=container, app=app)
    return app
```

`scripts/dishka/plot_dependencies_data.py` :

```python
"""Print the Dishka dependency graph in d2 format (https://d2lang.com)."""

import asyncio

from dishka import make_async_container
from dishka.plotter import render_d2

from app.providers import get_providers
from core.infrastructure.settings import Settings


async def main() -> None:
    container = make_async_container(*get_providers(), context={Settings: Settings()})
    try:
        print(render_d2(container))
    finally:
        await container.close()


if __name__ == "__main__":
    asyncio.run(main())
```

Dans `pyproject.toml`, section `[tool.mypy]` : `files = ["src", "tests", "scripts"]`.

- [ ] **Step 6: Vérifier le succès**

```bash
uv run pytest tests/unit -v
DATABASE__PASSWORD=unused make deps-graph | head -5
```

Expected : tous les tests passent ; le graphe d2 s'affiche sans erreur.

- [ ] **Step 7: Lint et commit**

```bash
make format && make lint
git add src scripts tests/unit pyproject.toml
git commit -m "feat(app): add application factory, problem details and health probes" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Alembic et harnais de tests d'intégration

**Files:**
- Create: `migrations/env.py`, `migrations/script.py.mako`, `migrations/versions/.gitkeep`, `src/app/models.py`
- Modify: `pyproject.toml` (`[tool.alembic]`, `[tool.mypy]`)
- Test: `tests/integration/__init__.py` (vide), `tests/integration/conftest.py`, `tests/integration/test_infrastructure.py`

**Interfaces:**
- Consumes: `Settings`, `DatabaseSettings`, `AppSettings`, `Environment` (Task 2) ; `Base` (Task 7) ; `create_app` (Task 8).
- Produces:
  - `app.models` : importe `Base` et chaque modèle ORM (complété en Tasks 12 et 16) ; `migrations/env.py` l'utilise comme `target_metadata`.
  - `migrations/env.py` lit l'URL dans `config.attributes["database_url"]` (tests) sinon dans `Settings().database.url`.
  - Fixtures d'intégration (`tests/integration/conftest.py`) : `postgres` (session), `database_settings` (session), `alembic_config` (session), `migrated_database -> DatabaseSettings` (session, après `alembic upgrade head`), `settings -> Settings`, `engine -> AsyncEngine`, `clean_database` (autouse, `TRUNCATE` de toutes les tables sauf `alembic_version`), `app -> FastAPI`, `container -> AsyncContainer` (conteneur Dishka APP de `app`), `client -> AsyncClient`.

- [ ] **Step 1: Configurer Alembic dans `pyproject.toml`**

Ajouter à la fin du fichier :

```toml
[tool.alembic]
script_location = "%(here)s/migrations"
file_template = "%%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d-%%(rev)s_%%(slug)s"

[[tool.alembic.post_write_hooks]]
name = "ruff"
type = "module"
module = "ruff"
options = "format REVISION_SCRIPT_FILENAME"
```

Remplacer dans `[tool.mypy]` la ligne `files` par :

```toml
files = ["src", "tests", "scripts", "migrations"]
exclude = ["^migrations/versions/"]
```

- [ ] **Step 2: Créer l'environnement Alembic**

`src/app/models.py` :

```python
"""Import every ORM model so that `Base.metadata` describes the whole schema."""

from core.infrastructure.db.base import Base

__all__ = ["Base"]
```

`migrations/env.py` :

```python
"""Alembic environment: application settings and metadata of every ORM model."""

import logging

from alembic import context
from sqlalchemy import URL, create_engine, pool

from app.models import Base
from core.infrastructure.settings import Settings

config = context.config
target_metadata = Base.metadata

if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)-5.5s %(message)s")


def database_url() -> URL:
    """URL injected by the tests through `config.attributes`, else from settings."""
    url = config.attributes.get("database_url")
    if isinstance(url, URL):
        return url
    return Settings().database.url


def run_migrations_offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(database_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata, compare_type=True
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

`migrations/script.py.mako` :

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
${imports if imports else ""}

revision: str = ${repr(up_revision)}
down_revision: str | Sequence[str] | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

Créer le fichier vide `migrations/versions/.gitkeep`.

- [ ] **Step 3: Écrire le harnais et les tests d'intégration**

`tests/integration/conftest.py` :

```python
"""PostgreSQL-backed fixtures. Requires Docker."""

from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import cast

import pytest
from alembic import command
from alembic.config import Config
from dishka import AsyncContainer
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from testcontainers.community.postgres import PostgresContainer

from app.main import create_app
from core.infrastructure.settings import (
    AppSettings,
    DatabaseSettings,
    Environment,
    Settings,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POSTGRES_IMAGE = "postgres:17-alpine"
LIST_TABLES = text(
    "SELECT tablename FROM pg_tables "
    "WHERE schemaname = 'public' AND tablename <> 'alembic_version'"
)


@pytest.fixture(scope="session")
def postgres() -> Iterator[PostgresContainer]:
    with PostgresContainer(POSTGRES_IMAGE, driver="psycopg") as container:
        yield container


@pytest.fixture(scope="session")
def database_settings(postgres: PostgresContainer) -> DatabaseSettings:
    return DatabaseSettings(
        host=postgres.get_container_host_ip(),
        port=int(postgres.get_exposed_port(5432)),
        user=postgres.username,
        password=SecretStr(postgres.password),
        name=postgres.dbname,
    )


@pytest.fixture(scope="session")
def alembic_config(database_settings: DatabaseSettings) -> Config:
    config = Config(toml_file=PROJECT_ROOT / "pyproject.toml")
    config.attributes["database_url"] = database_settings.url
    return config


@pytest.fixture(scope="session")
def migrated_database(
    database_settings: DatabaseSettings, alembic_config: Config
) -> DatabaseSettings:
    command.upgrade(alembic_config, "head")
    return database_settings


@pytest.fixture
def settings(migrated_database: DatabaseSettings) -> Settings:
    return Settings(
        app=AppSettings(environment=Environment.TEST),
        database=migrated_database,
        _env_file=None,
    )


@pytest.fixture
async def engine(migrated_database: DatabaseSettings) -> AsyncIterator[AsyncEngine]:
    async_engine = create_async_engine(migrated_database.url)
    yield async_engine
    await async_engine.dispose()


@pytest.fixture(autouse=True)
async def clean_database(engine: AsyncEngine) -> None:
    """Empty every application table before each test."""
    async with engine.begin() as connection:
        tables: list[str] = list((await connection.execute(LIST_TABLES)).scalars())
        if tables:
            quoted = ", ".join(f'"{name}"' for name in tables)
            await connection.execute(text(f"TRUNCATE {quoted} RESTART IDENTITY CASCADE"))


@pytest.fixture
async def app(settings: Settings) -> AsyncIterator[FastAPI]:
    application = create_app(settings)
    yield application
    await application.state.dishka_container.close()


@pytest.fixture
def container(app: FastAPI) -> AsyncContainer:
    """Application-scoped Dishka container; `async with container() as scope:`."""
    return cast(AsyncContainer, app.state.dishka_container)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
```

`tests/integration/test_infrastructure.py` :

```python
"""Readiness against a real database and consistency of migrations with models."""

from http import HTTPStatus

import pytest
from alembic import command
from alembic.config import Config
from httpx import AsyncClient


async def test_readiness_is_ok_when_the_database_is_reachable(
    client: AsyncClient,
) -> None:
    response = await client.get("/health/ready")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "ok"}


@pytest.mark.usefixtures("migrated_database")
async def test_migrations_match_the_orm_models(alembic_config: Config) -> None:
    command.check(alembic_config)
```

- [ ] **Step 4: Vérifier** (Docker doit tourner)

```bash
uv run pytest tests/integration -v
DATABASE__PASSWORD=unused uv run alembic history
```

Expected : 2 passed ; `alembic history` s'exécute sans erreur (aucune révision).

- [ ] **Step 5: Lint et commit**

```bash
make format && make lint
git add migrations src/app/models.py tests/integration pyproject.toml
git commit -m "feat: add Alembic environment and PostgreSQL integration test harness" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: `projects` — domaine

**Files:**
- Create (vides) : `src/modules/projects/domain/__init__.py`
- Create: `src/modules/projects/__init__.py`, `src/modules/projects/domain/enums.py`, `src/modules/projects/domain/errors.py`, `src/modules/projects/domain/events.py`, `src/modules/projects/domain/value_objects/{__init__,project_id,project_name,project_description}.py`, `src/modules/projects/domain/entities/{__init__,project}.py`, `src/modules/projects/domain/ports/{__init__,project_repository}.py`
- Test: `tests/unit/projects/__init__.py` (vide), `tests/unit/projects/factories.py`, `tests/unit/projects/test_project_domain.py`

**Interfaces:**
- Consumes: briques du domaine (Task 3), pagination (Task 4).
- Produces:
  - `modules.projects.domain.enums.ProjectStatus(StrEnum)` : `ACTIVE = "active"`, `ARCHIVED = "archived"`.
  - `modules.projects.domain.errors` : `ProjectNotFoundError(project_id: UUID)` (`project_not_found`), `ProjectNameAlreadyExistsError(name: str)` (`project_name_already_exists`), `ProjectAlreadyArchivedError(project_id)` (`project_already_archived`), `ProjectArchivedError(project_id)` (`project_archived`).
  - `modules.projects.domain.events` : `ProjectCreated(project_id: UUID, name: str)`, `ProjectArchived(project_id: UUID)`, `ProjectDeleted(project_id: UUID)`.
  - `modules.projects.domain.value_objects` : `ProjectId(EntityId)` ; `ProjectName(value: str)` (strip, 1..100, code `invalid_project_name`, constantes `MIN_LENGTH`, `MAX_LENGTH` dans `project_name.py`) ; `ProjectDescription(value: str)` (strip, ≤ 2000, code `invalid_project_description`, constante `MAX_LENGTH` dans `project_description.py`).
  - `modules.projects.domain.entities` : `ProjectProps(name, description, status)` ; `Project(AggregateRoot[ProjectId, ProjectProps])` avec `create(*, name, description="") -> Project`, `is_active: bool`, `rename(name)`, `change_description(description)`, `archive()`, `mark_deleted()`.
  - `modules.projects.domain.ports.ProjectRepositoryPort` (Protocol) : `add(entity)`, `save(entity)`, `delete(entity)`, `get_by_id(entity_id: ProjectId) -> Project | None`, `exists_by_name(name: ProjectName, *, exclude_id: ProjectId | None = None) -> bool`, `list_page(params, *, sort=None, filters=None, search=None) -> Page[Project]`.
  - Tests : `tests.unit.projects.factories` expose `PAST` et `make_project(*, name="Website", description="", status=ProjectStatus.ACTIVE) -> Project` (sans événement en attente, timestamps dans le passé).

- [ ] **Step 1: Écrire les tests qui échouent**

`tests/unit/projects/factories.py` :

```python
"""Builders of project aggregates for tests."""

from datetime import UTC, datetime

from modules.projects.domain.entities import Project, ProjectProps
from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.value_objects import (
    ProjectDescription,
    ProjectId,
    ProjectName,
)

PAST = datetime(2000, 1, 1, tzinfo=UTC)


def make_project(
    *,
    name: str = "Website",
    description: str = "",
    status: ProjectStatus = ProjectStatus.ACTIVE,
) -> Project:
    """A project as loaded from storage: no pending event, timestamps in the past."""
    return Project(
        id_=ProjectId.generate(),
        props=ProjectProps(
            name=ProjectName(name),
            description=ProjectDescription(description),
            status=status,
        ),
        created_at_=PAST,
        updated_at_=PAST,
    )
```

`tests/unit/projects/test_project_domain.py` :

```python
"""Value objects and aggregate of the projects module."""

from collections.abc import Callable

import pytest

from core.domain.errors import DomainValidationError
from modules.projects.domain.entities import Project
from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.errors import (
    ProjectAlreadyArchivedError,
    ProjectArchivedError,
)
from modules.projects.domain.events import (
    ProjectArchived,
    ProjectCreated,
    ProjectDeleted,
)
from modules.projects.domain.value_objects import ProjectDescription, ProjectName
from modules.projects.domain.value_objects.project_description import (
    MAX_LENGTH as DESCRIPTION_MAX_LENGTH,
)
from modules.projects.domain.value_objects.project_name import (
    MAX_LENGTH as NAME_MAX_LENGTH,
)
from tests.unit.projects.factories import PAST, make_project


class TestProjectName:
    def test_strips_surrounding_whitespace(self) -> None:
        assert ProjectName("  Website  ").value == "Website"

    @pytest.mark.parametrize("raw", ["", "   ", "x" * (NAME_MAX_LENGTH + 1)])
    def test_rejects_invalid_length(self, raw: str) -> None:
        with pytest.raises(DomainValidationError) as exc_info:
            ProjectName(raw)

        assert exc_info.value.code == "invalid_project_name"


class TestProjectDescription:
    def test_accepts_empty_text(self) -> None:
        assert ProjectDescription("").value == ""

    def test_rejects_too_long_text(self) -> None:
        with pytest.raises(DomainValidationError) as exc_info:
            ProjectDescription("x" * (DESCRIPTION_MAX_LENGTH + 1))

        assert exc_info.value.code == "invalid_project_description"


class TestProjectCreation:
    def test_create_builds_an_active_project_and_records_an_event(self) -> None:
        project = Project.create(name=" Website ", description="Marketing site")

        assert project.is_active
        assert project.props.name == ProjectName("Website")
        assert project.props.description == ProjectDescription("Marketing site")
        [event] = project.pull_events()
        assert isinstance(event, ProjectCreated)
        assert event.project_id == project.id_.value
        assert event.name == "Website"


class TestProjectChanges:
    def test_rename(self) -> None:
        project = make_project()

        project.rename("Intranet")

        assert project.props.name == ProjectName("Intranet")
        assert project.updated_at_ > PAST

    def test_change_description(self) -> None:
        project = make_project()

        project.change_description("New description")

        assert project.props.description == ProjectDescription("New description")
        assert project.updated_at_ > PAST

    def test_archive_changes_status_and_records_an_event(self) -> None:
        project = make_project()

        project.archive()

        assert project.props.status is ProjectStatus.ARCHIVED
        assert not project.is_active
        assert project.updated_at_ > PAST
        [event] = project.pull_events()
        assert isinstance(event, ProjectArchived)
        assert event.project_id == project.id_.value

    def test_archiving_twice_is_rejected(self) -> None:
        project = make_project(status=ProjectStatus.ARCHIVED)

        with pytest.raises(ProjectAlreadyArchivedError):
            project.archive()

    @pytest.mark.parametrize(
        "change",
        [
            lambda project: project.rename("Other"),
            lambda project: project.change_description("Other"),
        ],
    )
    def test_archived_project_is_read_only(
        self, change: Callable[[Project], None]
    ) -> None:
        project = make_project(status=ProjectStatus.ARCHIVED)

        with pytest.raises(ProjectArchivedError):
            change(project)

    def test_mark_deleted_records_an_event(self) -> None:
        project = make_project()

        project.mark_deleted()

        [event] = project.pull_events()
        assert isinstance(event, ProjectDeleted)
        assert event.project_id == project.id_.value
```

- [ ] **Step 2: Vérifier l'échec**

Run: `uv run pytest tests/unit/projects -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'modules.projects'`).

- [ ] **Step 3: Implémenter**

`src/modules/projects/__init__.py` :

```python
"""Projects module: named containers of work that can be archived or deleted."""
```

`src/modules/projects/domain/enums.py` :

```python
"""Enumerations of the projects module."""

from enum import StrEnum


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
```

`src/modules/projects/domain/errors.py` :

```python
"""Business errors of the projects module."""

from uuid import UUID

from core.domain.errors import (
    BusinessRuleViolationError,
    ConflictError,
    NotFoundError,
)


class ProjectNotFoundError(NotFoundError):
    def __init__(self, project_id: UUID) -> None:
        super().__init__(
            f"Project '{project_id}' was not found.",
            code="project_not_found",
            details={"project_id": str(project_id)},
        )


class ProjectNameAlreadyExistsError(ConflictError):
    def __init__(self, name: str) -> None:
        super().__init__(
            f"A project named '{name}' already exists.",
            code="project_name_already_exists",
            details={"name": name},
        )


class ProjectAlreadyArchivedError(BusinessRuleViolationError):
    def __init__(self, project_id: UUID) -> None:
        super().__init__(
            f"Project '{project_id}' is already archived.",
            code="project_already_archived",
            details={"project_id": str(project_id)},
        )


class ProjectArchivedError(BusinessRuleViolationError):
    def __init__(self, project_id: UUID) -> None:
        super().__init__(
            f"Project '{project_id}' is archived and cannot be modified.",
            code="project_archived",
            details={"project_id": str(project_id)},
        )
```

`src/modules/projects/domain/events.py` :

```python
"""Domain events of the projects module (public: see `modules.projects.public`)."""

from dataclasses import dataclass
from uuid import UUID

from core.domain.events import DomainEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectCreated(DomainEvent):
    project_id: UUID
    name: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectArchived(DomainEvent):
    project_id: UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectDeleted(DomainEvent):
    project_id: UUID
```

`src/modules/projects/domain/value_objects/project_id.py` :

```python
"""Project identifier."""

from dataclasses import dataclass

from core.domain.identifier import EntityId


@dataclass(frozen=True, slots=True, repr=False)
class ProjectId(EntityId):
    """Identity of a project."""
```

`src/modules/projects/domain/value_objects/project_name.py` :

```python
"""Project name."""

from dataclasses import dataclass
from typing import Final

from core.domain.errors import DomainValidationError
from core.domain.value_object import ValueObject

MIN_LENGTH: Final[int] = 1
MAX_LENGTH: Final[int] = 100


@dataclass(frozen=True, slots=True, repr=False)
class ProjectName(ValueObject):
    """Unique human-readable name; surrounding whitespace is removed."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not MIN_LENGTH <= len(normalized) <= MAX_LENGTH:
            raise DomainValidationError(
                f"Project name must be {MIN_LENGTH} to {MAX_LENGTH} characters long.",
                code="invalid_project_name",
                details={"min_length": MIN_LENGTH, "max_length": MAX_LENGTH},
            )
        object.__setattr__(self, "value", normalized)
```

`src/modules/projects/domain/value_objects/project_description.py` :

```python
"""Project description."""

from dataclasses import dataclass
from typing import Final

from core.domain.errors import DomainValidationError
from core.domain.value_object import ValueObject

MAX_LENGTH: Final[int] = 2000


@dataclass(frozen=True, slots=True, repr=False)
class ProjectDescription(ValueObject):
    """Free text, possibly empty; surrounding whitespace is removed."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if len(normalized) > MAX_LENGTH:
            raise DomainValidationError(
                f"Project description cannot exceed {MAX_LENGTH} characters.",
                code="invalid_project_description",
                details={"max_length": MAX_LENGTH},
            )
        object.__setattr__(self, "value", normalized)
```

`src/modules/projects/domain/value_objects/__init__.py` :

```python
from .project_description import ProjectDescription
from .project_id import ProjectId
from .project_name import ProjectName

__all__ = ["ProjectDescription", "ProjectId", "ProjectName"]
```

`src/modules/projects/domain/entities/project.py` :

```python
"""Project aggregate."""

from dataclasses import dataclass
from typing import Self

from core.domain.aggregate_root import AggregateRoot
from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.errors import (
    ProjectAlreadyArchivedError,
    ProjectArchivedError,
)
from modules.projects.domain.events import (
    ProjectArchived,
    ProjectCreated,
    ProjectDeleted,
)
from modules.projects.domain.value_objects import (
    ProjectDescription,
    ProjectId,
    ProjectName,
)


@dataclass(slots=True)
class ProjectProps:
    name: ProjectName
    description: ProjectDescription
    status: ProjectStatus


class Project(AggregateRoot[ProjectId, ProjectProps]):
    """A named container of work. Archived projects are read-only."""

    @classmethod
    def create(cls, *, name: str, description: str = "") -> Self:
        project = cls(
            id_=ProjectId.generate(),
            props=ProjectProps(
                name=ProjectName(name),
                description=ProjectDescription(description),
                status=ProjectStatus.ACTIVE,
            ),
        )
        project.record_event(
            ProjectCreated(project_id=project.id_.value, name=project.props.name.value)
        )
        return project

    @property
    def is_active(self) -> bool:
        return self.props.status is ProjectStatus.ACTIVE

    def rename(self, name: str) -> None:
        self._ensure_active()
        self.props.name = ProjectName(name)
        self.touch()

    def change_description(self, description: str) -> None:
        self._ensure_active()
        self.props.description = ProjectDescription(description)
        self.touch()

    def archive(self) -> None:
        if not self.is_active:
            raise ProjectAlreadyArchivedError(self.id_.value)
        self.props.status = ProjectStatus.ARCHIVED
        self.touch()
        self.record_event(ProjectArchived(project_id=self.id_.value))

    def mark_deleted(self) -> None:
        """Announce the deletion; the repository removes the row."""
        self.record_event(ProjectDeleted(project_id=self.id_.value))

    def validate(self) -> None:
        """Invariants are enforced by the value objects."""

    def _ensure_active(self) -> None:
        if not self.is_active:
            raise ProjectArchivedError(self.id_.value)
```

`src/modules/projects/domain/entities/__init__.py` :

```python
from .project import Project, ProjectProps

__all__ = ["Project", "ProjectProps"]
```

`src/modules/projects/domain/ports/project_repository.py` :

```python
"""Persistence port of the project aggregate."""

from collections.abc import Mapping
from typing import Protocol

from core.domain.pagination import Page, PageParams, Sort
from modules.projects.domain.entities import Project
from modules.projects.domain.value_objects import ProjectId, ProjectName


class ProjectRepositoryPort(Protocol):
    async def add(self, entity: Project) -> None: ...

    async def save(self, entity: Project) -> None: ...

    async def delete(self, entity: Project) -> None: ...

    async def get_by_id(self, entity_id: ProjectId) -> Project | None: ...

    async def exists_by_name(
        self, name: ProjectName, *, exclude_id: ProjectId | None = None
    ) -> bool: ...

    async def list_page(
        self,
        params: PageParams,
        *,
        sort: Sort | None = None,
        filters: Mapping[str, object] | None = None,
        search: str | None = None,
    ) -> Page[Project]: ...
```

`src/modules/projects/domain/ports/__init__.py` :

```python
from .project_repository import ProjectRepositoryPort

__all__ = ["ProjectRepositoryPort"]
```

- [ ] **Step 4: Vérifier le succès**

Run: `uv run pytest tests/unit/projects -v`
Expected: tous les tests passent.

- [ ] **Step 5: Lint et commit**

```bash
make format && make lint
git add src/modules/projects tests/unit/projects
git commit -m "feat(projects): add project domain model" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 11: `projects` — use cases et API publique

**Files:**
- Create: `src/modules/projects/application/__init__.py` (vide), `src/modules/projects/application/dto.py`, `src/modules/projects/application/commands/{__init__,create_project,update_project,archive_project,delete_project}.py`, `src/modules/projects/application/queries/{__init__,get_project_by_id,list_projects}.py`, `src/modules/projects/public.py`
- Test: `tests/fakes/__init__.py` (vide), `tests/fakes/unit_of_work.py`, `tests/fakes/projects.py`, `tests/unit/projects/test_project_use_cases.py`

**Interfaces:**
- Consumes: domaine `projects` (Task 10), `UnitOfWork` (Task 4), `Page`, `PageParams`, `Sort` (Task 4).
- Produces:
  - `modules.projects.application.dto.ProjectDTO(id, name, description, status, created_at, updated_at)` avec `from_entity(project) -> ProjectDTO`.
  - Commandes (constructeur `(repository: ProjectRepositoryPort, uow: UnitOfWork)`, méthode `execute(request)`) : `CreateProjectCommand` + `CreateProjectRequest(name, description="")` → `ProjectDTO` ; `UpdateProjectCommand` + `UpdateProjectRequest(project_id, name=None, description=None)` → `ProjectDTO` ; `ArchiveProjectCommand` + `ArchiveProjectRequest(project_id)` → `ProjectDTO` ; `DeleteProjectCommand` + `DeleteProjectRequest(project_id)` → `None`.
  - Requêtes (constructeur `(repository: ProjectRepositoryPort)`) : `GetProjectByIdQuery` + `GetProjectByIdRequest(project_id)` → `ProjectDTO` ; `ListProjectsQuery` + `ListProjectsRequest(page=1, size=20, status=None, search=None, sort="-created_at")` → `Page[ProjectDTO]` (filtre `{"status": status.value}` si fourni).
  - `modules.projects.public` : `ProjectSummary(id: UUID, name: str, is_active: bool)`, `ProjectsPublicApi(repository: ProjectRepositoryPort)` avec `get_summary(project_id: UUID) -> ProjectSummary | None` ; ré-exporte `ProjectArchived`, `ProjectDeleted`.
  - Doublures de test : `tests.fakes.unit_of_work.FakeUnitOfWork` (`commits`, `rollbacks`) ; `tests.fakes.projects.InMemoryProjectRepository(*projects)` (`projects: dict[UUID, Project]`, `deleted: list[Project]`, `list_calls: list[dict[str, object]]`).

- [ ] **Step 1: Écrire les doublures et les tests qui échouent**

`tests/fakes/unit_of_work.py` :

```python
"""Unit of work double."""

from core.application.unit_of_work import UnitOfWork


class FakeUnitOfWork(UnitOfWork):
    def __init__(self) -> None:
        self.commits = 0
        self.rollbacks = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1
```

`tests/fakes/projects.py` :

```python
"""In-memory doubles of the projects module."""

from collections.abc import Mapping
from uuid import UUID

from core.domain.pagination import Page, PageParams, Sort
from modules.projects.domain.entities import Project
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.domain.value_objects import ProjectId, ProjectName


class InMemoryProjectRepository(ProjectRepositoryPort):
    """Dictionary-backed repository; `list_page` records its arguments, never sorts."""

    def __init__(self, *projects: Project) -> None:
        self.projects: dict[UUID, Project] = {p.id_.value: p for p in projects}
        self.deleted: list[Project] = []
        self.list_calls: list[dict[str, object]] = []

    async def add(self, entity: Project) -> None:
        self.projects[entity.id_.value] = entity

    async def save(self, entity: Project) -> None:
        self.projects[entity.id_.value] = entity

    async def delete(self, entity: Project) -> None:
        self.projects.pop(entity.id_.value, None)
        self.deleted.append(entity)

    async def get_by_id(self, entity_id: ProjectId) -> Project | None:
        return self.projects.get(entity_id.value)

    async def exists_by_name(
        self, name: ProjectName, *, exclude_id: ProjectId | None = None
    ) -> bool:
        return any(
            project.props.name == name and project.id_ != exclude_id
            for project in self.projects.values()
        )

    async def list_page(
        self,
        params: PageParams,
        *,
        sort: Sort | None = None,
        filters: Mapping[str, object] | None = None,
        search: str | None = None,
    ) -> Page[Project]:
        self.list_calls.append(
            {"params": params, "sort": sort, "filters": filters, "search": search}
        )
        projects = list(self.projects.values())
        return Page(
            items=projects[params.offset : params.offset + params.size],
            total=len(projects),
            page=params.page,
            size=params.size,
        )
```

`tests/unit/projects/test_project_use_cases.py` :

```python
"""Commands, queries and public API of the projects module."""

from uuid import uuid4

import pytest

from core.domain.pagination import PageParams, Sort, SortDirection
from modules.projects.application.commands import (
    ArchiveProjectCommand,
    ArchiveProjectRequest,
    CreateProjectCommand,
    CreateProjectRequest,
    DeleteProjectCommand,
    DeleteProjectRequest,
    UpdateProjectCommand,
    UpdateProjectRequest,
)
from modules.projects.application.dto import ProjectDTO
from modules.projects.application.queries import (
    GetProjectByIdQuery,
    GetProjectByIdRequest,
    ListProjectsQuery,
    ListProjectsRequest,
)
from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.errors import (
    ProjectArchivedError,
    ProjectNameAlreadyExistsError,
    ProjectNotFoundError,
)
from modules.projects.domain.events import ProjectArchived, ProjectDeleted
from modules.projects.public import ProjectsPublicApi, ProjectSummary
from tests.fakes.projects import InMemoryProjectRepository
from tests.fakes.unit_of_work import FakeUnitOfWork
from tests.unit.projects.factories import make_project


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


class TestCreateProject:
    async def test_creates_an_active_project(self, uow: FakeUnitOfWork) -> None:
        repository = InMemoryProjectRepository()

        result = await CreateProjectCommand(repository, uow).execute(
            CreateProjectRequest(name="Website", description="Marketing site")
        )

        assert (result.name, result.description) == ("Website", "Marketing site")
        assert result.status is ProjectStatus.ACTIVE
        assert result.id in repository.projects
        assert uow.commits == 1

    async def test_rejects_a_name_already_used(self, uow: FakeUnitOfWork) -> None:
        repository = InMemoryProjectRepository(make_project(name="Website"))

        with pytest.raises(ProjectNameAlreadyExistsError):
            await CreateProjectCommand(repository, uow).execute(
                CreateProjectRequest(name="  Website ")
            )

        assert uow.commits == 0


class TestUpdateProject:
    async def test_updates_name_and_description(self, uow: FakeUnitOfWork) -> None:
        project = make_project()
        repository = InMemoryProjectRepository(project)

        result = await UpdateProjectCommand(repository, uow).execute(
            UpdateProjectRequest(
                project_id=project.id_.value, name="Intranet", description="Internal"
            )
        )

        assert (result.name, result.description) == ("Intranet", "Internal")
        assert uow.commits == 1

    async def test_keeping_the_same_name_is_allowed(self, uow: FakeUnitOfWork) -> None:
        project = make_project(name="Website")
        repository = InMemoryProjectRepository(project)

        result = await UpdateProjectCommand(repository, uow).execute(
            UpdateProjectRequest(project_id=project.id_.value, name="Website")
        )

        assert result.name == "Website"

    async def test_rejects_a_name_used_by_another_project(
        self, uow: FakeUnitOfWork
    ) -> None:
        project = make_project(name="Website")
        repository = InMemoryProjectRepository(project, make_project(name="Intranet"))

        with pytest.raises(ProjectNameAlreadyExistsError):
            await UpdateProjectCommand(repository, uow).execute(
                UpdateProjectRequest(project_id=project.id_.value, name="Intranet")
            )

        assert uow.commits == 0

    async def test_unknown_project(self, uow: FakeUnitOfWork) -> None:
        with pytest.raises(ProjectNotFoundError):
            await UpdateProjectCommand(InMemoryProjectRepository(), uow).execute(
                UpdateProjectRequest(project_id=uuid4(), name="Other")
            )

    async def test_archived_project_cannot_be_updated(
        self, uow: FakeUnitOfWork
    ) -> None:
        project = make_project(status=ProjectStatus.ARCHIVED)

        with pytest.raises(ProjectArchivedError):
            await UpdateProjectCommand(InMemoryProjectRepository(project), uow).execute(
                UpdateProjectRequest(project_id=project.id_.value, description="x")
            )


class TestArchiveProject:
    async def test_archives_and_commits(self, uow: FakeUnitOfWork) -> None:
        project = make_project()
        repository = InMemoryProjectRepository(project)

        result = await ArchiveProjectCommand(repository, uow).execute(
            ArchiveProjectRequest(project_id=project.id_.value)
        )

        assert result.status is ProjectStatus.ARCHIVED
        assert uow.commits == 1
        assert [type(event) for event in project.pull_events()] == [ProjectArchived]

    async def test_unknown_project(self, uow: FakeUnitOfWork) -> None:
        with pytest.raises(ProjectNotFoundError):
            await ArchiveProjectCommand(InMemoryProjectRepository(), uow).execute(
                ArchiveProjectRequest(project_id=uuid4())
            )


class TestDeleteProject:
    async def test_deletes_and_records_an_event(self, uow: FakeUnitOfWork) -> None:
        project = make_project()
        repository = InMemoryProjectRepository(project)

        await DeleteProjectCommand(repository, uow).execute(
            DeleteProjectRequest(project_id=project.id_.value)
        )

        assert repository.deleted == [project]
        assert repository.projects == {}
        assert uow.commits == 1
        assert [type(event) for event in project.pull_events()] == [ProjectDeleted]

    async def test_unknown_project(self, uow: FakeUnitOfWork) -> None:
        with pytest.raises(ProjectNotFoundError):
            await DeleteProjectCommand(InMemoryProjectRepository(), uow).execute(
                DeleteProjectRequest(project_id=uuid4())
            )


class TestProjectQueries:
    async def test_get_by_id(self) -> None:
        project = make_project(name="Website")

        result = await GetProjectByIdQuery(InMemoryProjectRepository(project)).execute(
            GetProjectByIdRequest(project_id=project.id_.value)
        )

        assert result == ProjectDTO.from_entity(project)

    async def test_get_unknown_project(self) -> None:
        with pytest.raises(ProjectNotFoundError):
            await GetProjectByIdQuery(InMemoryProjectRepository()).execute(
                GetProjectByIdRequest(project_id=uuid4())
            )

    async def test_list_translates_the_request_for_the_repository(self) -> None:
        repository = InMemoryProjectRepository(
            make_project(name="Alpha"), make_project(name="Beta")
        )

        page = await ListProjectsQuery(repository).execute(
            ListProjectsRequest(
                page=1, size=1, status=ProjectStatus.ACTIVE, search="Al", sort="name"
            )
        )

        assert repository.list_calls == [
            {
                "params": PageParams(page=1, size=1),
                "sort": Sort("name", SortDirection.ASC),
                "filters": {"status": "active"},
                "search": "Al",
            }
        ]
        assert (page.total, page.pages) == (2, 2)
        assert all(isinstance(item, ProjectDTO) for item in page.items)

    async def test_list_defaults(self) -> None:
        repository = InMemoryProjectRepository()

        await ListProjectsQuery(repository).execute(ListProjectsRequest())

        assert repository.list_calls == [
            {
                "params": PageParams(page=1, size=20),
                "sort": Sort("created_at", SortDirection.DESC),
                "filters": {},
                "search": None,
            }
        ]


class TestProjectsPublicApi:
    async def test_returns_a_summary(self) -> None:
        project = make_project(name="Website", status=ProjectStatus.ARCHIVED)
        api = ProjectsPublicApi(InMemoryProjectRepository(project))

        summary = await api.get_summary(project.id_.value)

        assert summary == ProjectSummary(
            id=project.id_.value, name="Website", is_active=False
        )

    async def test_returns_none_for_an_unknown_project(self) -> None:
        api = ProjectsPublicApi(InMemoryProjectRepository())

        assert await api.get_summary(uuid4()) is None
```

- [ ] **Step 2: Vérifier l'échec**

Run: `uv run pytest tests/unit/projects/test_project_use_cases.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'modules.projects.application'`).

- [ ] **Step 3: Implémenter la couche application**

`src/modules/projects/application/dto.py` :

```python
"""Data returned by the use cases of the projects module."""

from dataclasses import dataclass
from datetime import datetime
from typing import Self
from uuid import UUID

from modules.projects.domain.entities import Project
from modules.projects.domain.enums import ProjectStatus


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectDTO:
    id: UUID
    name: str
    description: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, project: Project) -> Self:
        return cls(
            id=project.id_.value,
            name=project.props.name.value,
            description=project.props.description.value,
            status=project.props.status,
            created_at=project.created_at_,
            updated_at=project.updated_at_,
        )
```

`src/modules/projects/application/commands/create_project.py` :

```python
"""Create a project."""

import logging
from dataclasses import dataclass

from core.application.unit_of_work import UnitOfWork
from modules.projects.application.dto import ProjectDTO
from modules.projects.domain.entities import Project
from modules.projects.domain.errors import ProjectNameAlreadyExistsError
from modules.projects.domain.ports import ProjectRepositoryPort

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateProjectRequest:
    name: str
    description: str = ""


class CreateProjectCommand:
    """Create an active project. Project names are unique."""

    def __init__(self, repository: ProjectRepositoryPort, uow: UnitOfWork) -> None:
        self._repository = repository
        self._uow = uow

    async def execute(self, request: CreateProjectRequest) -> ProjectDTO:
        project = Project.create(name=request.name, description=request.description)
        if await self._repository.exists_by_name(project.props.name):
            raise ProjectNameAlreadyExistsError(project.props.name.value)
        await self._repository.add(project)
        await self._uow.commit()
        log.info("Project created: %s", project.id_.value)
        return ProjectDTO.from_entity(project)
```

`src/modules/projects/application/commands/update_project.py` :

```python
"""Update the name and/or description of a project."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.application.unit_of_work import UnitOfWork
from modules.projects.application.dto import ProjectDTO
from modules.projects.domain.errors import (
    ProjectNameAlreadyExistsError,
    ProjectNotFoundError,
)
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.domain.value_objects import ProjectId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateProjectRequest:
    project_id: UUID
    name: str | None = None
    description: str | None = None


class UpdateProjectCommand:
    """Rename a project and/or change its description (active projects only)."""

    def __init__(self, repository: ProjectRepositoryPort, uow: UnitOfWork) -> None:
        self._repository = repository
        self._uow = uow

    async def execute(self, request: UpdateProjectRequest) -> ProjectDTO:
        project = await self._repository.get_by_id(ProjectId(request.project_id))
        if project is None:
            raise ProjectNotFoundError(request.project_id)
        if request.name is not None:
            project.rename(request.name)
            if await self._repository.exists_by_name(
                project.props.name, exclude_id=project.id_
            ):
                raise ProjectNameAlreadyExistsError(project.props.name.value)
        if request.description is not None:
            project.change_description(request.description)
        await self._repository.save(project)
        await self._uow.commit()
        log.info("Project updated: %s", request.project_id)
        return ProjectDTO.from_entity(project)
```

`src/modules/projects/application/commands/archive_project.py` :

```python
"""Archive a project."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.application.unit_of_work import UnitOfWork
from modules.projects.application.dto import ProjectDTO
from modules.projects.domain.errors import ProjectNotFoundError
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.domain.value_objects import ProjectId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ArchiveProjectRequest:
    project_id: UUID


class ArchiveProjectCommand:
    """Archive a project and publish `ProjectArchived`."""

    def __init__(self, repository: ProjectRepositoryPort, uow: UnitOfWork) -> None:
        self._repository = repository
        self._uow = uow

    async def execute(self, request: ArchiveProjectRequest) -> ProjectDTO:
        project = await self._repository.get_by_id(ProjectId(request.project_id))
        if project is None:
            raise ProjectNotFoundError(request.project_id)
        project.archive()
        await self._repository.save(project)
        await self._uow.commit()
        log.info("Project archived: %s", request.project_id)
        return ProjectDTO.from_entity(project)
```

`src/modules/projects/application/commands/delete_project.py` :

```python
"""Delete a project."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.application.unit_of_work import UnitOfWork
from modules.projects.domain.errors import ProjectNotFoundError
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.domain.value_objects import ProjectId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteProjectRequest:
    project_id: UUID


class DeleteProjectCommand:
    """Delete a project and publish `ProjectDeleted`."""

    def __init__(self, repository: ProjectRepositoryPort, uow: UnitOfWork) -> None:
        self._repository = repository
        self._uow = uow

    async def execute(self, request: DeleteProjectRequest) -> None:
        project = await self._repository.get_by_id(ProjectId(request.project_id))
        if project is None:
            raise ProjectNotFoundError(request.project_id)
        project.mark_deleted()
        await self._repository.delete(project)
        await self._uow.commit()
        log.info("Project deleted: %s", request.project_id)
```

`src/modules/projects/application/commands/__init__.py` :

```python
from .archive_project import ArchiveProjectCommand, ArchiveProjectRequest
from .create_project import CreateProjectCommand, CreateProjectRequest
from .delete_project import DeleteProjectCommand, DeleteProjectRequest
from .update_project import UpdateProjectCommand, UpdateProjectRequest

__all__ = [
    "ArchiveProjectCommand",
    "ArchiveProjectRequest",
    "CreateProjectCommand",
    "CreateProjectRequest",
    "DeleteProjectCommand",
    "DeleteProjectRequest",
    "UpdateProjectCommand",
    "UpdateProjectRequest",
]
```

`src/modules/projects/application/queries/get_project_by_id.py` :

```python
"""Get one project."""

from dataclasses import dataclass
from uuid import UUID

from modules.projects.application.dto import ProjectDTO
from modules.projects.domain.errors import ProjectNotFoundError
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.domain.value_objects import ProjectId


@dataclass(frozen=True, slots=True, kw_only=True)
class GetProjectByIdRequest:
    project_id: UUID


class GetProjectByIdQuery:
    """Return one project."""

    def __init__(self, repository: ProjectRepositoryPort) -> None:
        self._repository = repository

    async def execute(self, request: GetProjectByIdRequest) -> ProjectDTO:
        project = await self._repository.get_by_id(ProjectId(request.project_id))
        if project is None:
            raise ProjectNotFoundError(request.project_id)
        return ProjectDTO.from_entity(project)
```

`src/modules/projects/application/queries/list_projects.py` :

```python
"""List projects."""

from dataclasses import dataclass

from core.domain.pagination import Page, PageParams, Sort
from modules.projects.application.dto import ProjectDTO
from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.ports import ProjectRepositoryPort


@dataclass(frozen=True, slots=True, kw_only=True)
class ListProjectsRequest:
    page: int = 1
    size: int = 20
    status: ProjectStatus | None = None
    search: str | None = None
    sort: str = "-created_at"


class ListProjectsQuery:
    """Return a page of projects, optionally filtered by status and name."""

    def __init__(self, repository: ProjectRepositoryPort) -> None:
        self._repository = repository

    async def execute(self, request: ListProjectsRequest) -> Page[ProjectDTO]:
        filters: dict[str, object] = {}
        if request.status is not None:
            filters["status"] = request.status.value
        page = await self._repository.list_page(
            PageParams(page=request.page, size=request.size),
            sort=Sort.parse(request.sort),
            filters=filters,
            search=request.search,
        )
        return page.map(ProjectDTO.from_entity)
```

`src/modules/projects/application/queries/__init__.py` :

```python
from .get_project_by_id import GetProjectByIdQuery, GetProjectByIdRequest
from .list_projects import ListProjectsQuery, ListProjectsRequest

__all__ = [
    "GetProjectByIdQuery",
    "GetProjectByIdRequest",
    "ListProjectsQuery",
    "ListProjectsRequest",
]
```

`src/modules/projects/public.py` :

```python
"""
Public API of the projects module.

Other modules may import this file only. It never exposes domain objects.
"""

from dataclasses import dataclass
from uuid import UUID

from modules.projects.domain.events import ProjectArchived, ProjectDeleted
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.domain.value_objects import ProjectId

__all__ = ["ProjectArchived", "ProjectDeleted", "ProjectSummary", "ProjectsPublicApi"]


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectSummary:
    id: UUID
    name: str
    is_active: bool


class ProjectsPublicApi:
    """Read-only facade used by other modules."""

    def __init__(self, repository: ProjectRepositoryPort) -> None:
        self._repository = repository

    async def get_summary(self, project_id: UUID) -> ProjectSummary | None:
        project = await self._repository.get_by_id(ProjectId(project_id))
        if project is None:
            return None
        return ProjectSummary(
            id=project.id_.value,
            name=project.props.name.value,
            is_active=project.is_active,
        )
```

- [ ] **Step 4: Vérifier le succès**

Run: `uv run pytest tests/unit -v`
Expected: tout passe.

- [ ] **Step 5: Lint et commit**

```bash
make format && make lint
git add src/modules/projects tests/fakes tests/unit/projects
git commit -m "feat(projects): add project use cases and public API" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 12: `projects` — persistance, migration initiale et provider

**Files:**
- Create: `src/modules/projects/infrastructure/__init__.py` (vide), `src/modules/projects/infrastructure/models/{__init__,project_model}.py`, `src/modules/projects/infrastructure/mappers/{__init__,project_mapper}.py`, `src/modules/projects/infrastructure/repositories/{__init__,project_repository}.py`, `src/modules/projects/provider.py`, `migrations/versions/2026_09_17_1200-0001_initial_schema.py`
- Modify: `src/app/models.py`, `src/app/providers.py`
- Delete: `migrations/versions/.gitkeep`
- Test: `tests/integration/projects/__init__.py` (vide), `tests/integration/projects/test_project_repository.py`

**Interfaces:**
- Consumes: `Base`, mixins, `SqlaRepository`, `EntityMapper` (Task 7) ; `AggregateTracker` (Task 5) ; domaine et application `projects` (Tasks 10-11) ; fixtures `container`, `migrated_database` (Task 9).
- Produces:
  - Table `projects` : `id` uuid PK (`pk_projects`), `name` varchar(100) unique (`uq_projects_name`), `description` text, `status` varchar(20) indexé (`ix_projects_status`) + CHECK (`ck_projects_status`), `created_at`, `updated_at` timestamptz ; tous NOT NULL.
  - `ProjectModel`, `ProjectMapper`, `SqlaProjectRepository(session, tracker)` (tri : `name`, `created_at`, `updated_at` ; filtre : `status` ; recherche : `name`).
  - `modules.projects.provider.ProjectsProvider` (REQUEST) : `ProjectRepositoryPort`, les 6 use cases, `ProjectsPublicApi`.
  - Révision Alembic `0001` (sera complétée par la table `tasks` en Task 16).

- [ ] **Step 1: Écrire les tests d'intégration qui échouent**

`tests/integration/projects/test_project_repository.py` :

```python
"""SqlaProjectRepository and the unit of work against PostgreSQL."""

from collections.abc import Sequence

import pytest
from dishka import AsyncContainer

from core.application.unit_of_work import UnitOfWork
from core.domain.errors import ConflictError, DomainValidationError
from core.domain.pagination import PageParams, Sort, SortDirection
from modules.projects.domain.entities import Project
from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.domain.value_objects import ProjectName


async def persist(container: AsyncContainer, projects: Sequence[Project]) -> None:
    async with container() as scope:
        repository = await scope.get(ProjectRepositoryPort)
        for project in projects:
            await repository.add(project)
        await (await scope.get(UnitOfWork)).commit()


async def test_add_then_get_by_id_round_trips_every_field(
    container: AsyncContainer,
) -> None:
    project = Project.create(name="Website", description="Marketing site")
    await persist(container, [project])

    async with container() as scope:
        loaded = await (await scope.get(ProjectRepositoryPort)).get_by_id(project.id_)

    assert loaded is not None
    assert loaded.props == project.props
    assert loaded.created_at_ == project.created_at_
    assert loaded.updated_at_ == project.updated_at_


async def test_save_persists_changes(container: AsyncContainer) -> None:
    project = Project.create(name="Website")
    await persist(container, [project])

    async with container() as scope:
        repository = await scope.get(ProjectRepositoryPort)
        loaded = await repository.get_by_id(project.id_)
        assert loaded is not None
        loaded.rename("Intranet")
        loaded.archive()
        await repository.save(loaded)
        await (await scope.get(UnitOfWork)).commit()

    async with container() as scope:
        reloaded = await (await scope.get(ProjectRepositoryPort)).get_by_id(project.id_)
    assert reloaded is not None
    assert reloaded.props.name == ProjectName("Intranet")
    assert reloaded.props.status is ProjectStatus.ARCHIVED


async def test_delete_removes_the_row(container: AsyncContainer) -> None:
    project = Project.create(name="Website")
    await persist(container, [project])

    async with container() as scope:
        repository = await scope.get(ProjectRepositoryPort)
        loaded = await repository.get_by_id(project.id_)
        assert loaded is not None
        await repository.delete(loaded)
        await (await scope.get(UnitOfWork)).commit()

    async with container() as scope:
        repository = await scope.get(ProjectRepositoryPort)
        assert await repository.get_by_id(project.id_) is None


async def test_exists_by_name_can_exclude_a_project(container: AsyncContainer) -> None:
    project = Project.create(name="Website")
    await persist(container, [project])

    async with container() as scope:
        repository = await scope.get(ProjectRepositoryPort)
        assert await repository.exists_by_name(ProjectName("Website"))
        assert not await repository.exists_by_name(
            ProjectName("Website"), exclude_id=project.id_
        )
        assert not await repository.exists_by_name(ProjectName("Intranet"))


async def test_unique_name_violation_is_reported_as_a_conflict(
    container: AsyncContainer,
) -> None:
    async with container() as scope:
        repository = await scope.get(ProjectRepositoryPort)
        await repository.add(Project.create(name="Website"))
        await repository.add(Project.create(name="Website"))
        with pytest.raises(ConflictError) as exc_info:
            await (await scope.get(UnitOfWork)).commit()

    assert exc_info.value.code == "unique_violation"
    assert exc_info.value.details == {"constraint": "uq_projects_name"}


async def test_list_page_filters_sorts_and_paginates(container: AsyncContainer) -> None:
    alpha, beta, gamma = (Project.create(name=name) for name in ("Alpha", "Beta", "Gamma"))
    beta.archive()
    await persist(container, [gamma, alpha, beta])

    async with container() as scope:
        page = await (await scope.get(ProjectRepositoryPort)).list_page(
            PageParams(page=2, size=1),
            sort=Sort("name", SortDirection.ASC),
            filters={"status": ProjectStatus.ACTIVE.value},
        )

    assert [project.props.name.value for project in page.items] == ["Gamma"]
    assert (page.total, page.pages) == (2, 2)


async def test_list_page_search_matches_wildcards_literally(
    container: AsyncContainer,
) -> None:
    await persist(
        container, [Project.create(name="50% off"), Project.create(name="500 offers")]
    )

    async with container() as scope:
        page = await (await scope.get(ProjectRepositoryPort)).list_page(
            PageParams(), search="50%"
        )

    assert [project.props.name.value for project in page.items] == ["50% off"]


async def test_list_page_rejects_a_field_outside_the_whitelist(
    container: AsyncContainer,
) -> None:
    async with container() as scope:
        repository = await scope.get(ProjectRepositoryPort)
        with pytest.raises(DomainValidationError):
            await repository.list_page(PageParams(), sort=Sort("description"))
```

- [ ] **Step 2: Vérifier l'échec**

Run: `uv run pytest tests/integration/projects -v`
Expected: FAIL (`NoFactoryError` / `ModuleNotFoundError` : `ProjectRepositoryPort` n'est pas fourni).

- [ ] **Step 3: Implémenter la persistance**

`src/modules/projects/infrastructure/models/project_model.py` :

```python
"""ORM model of the `projects` table."""

from sqlalchemy import CheckConstraint, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.infrastructure.db.base import Base
from core.infrastructure.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from modules.projects.domain.enums import ProjectStatus

STATUS_VALUES = ", ".join(f"'{status.value}'" for status in ProjectStatus)


class ProjectModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (CheckConstraint(f"status IN ({STATUS_VALUES})", name="status"),)

    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), index=True)
```

`src/modules/projects/infrastructure/models/__init__.py` :

```python
from .project_model import ProjectModel

__all__ = ["ProjectModel"]
```

`src/modules/projects/infrastructure/mappers/project_mapper.py` :

```python
"""Mapping between `Project` and `ProjectModel`."""

from core.infrastructure.db.mapper import EntityMapper
from modules.projects.domain.entities import Project, ProjectProps
from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.value_objects import (
    ProjectDescription,
    ProjectId,
    ProjectName,
)
from modules.projects.infrastructure.models import ProjectModel


class ProjectMapper(EntityMapper[Project, ProjectModel]):
    def to_model(self, entity: Project) -> ProjectModel:
        return ProjectModel(
            id=entity.id_.value,
            name=entity.props.name.value,
            description=entity.props.description.value,
            status=entity.props.status.value,
            created_at=entity.created_at_,
            updated_at=entity.updated_at_,
        )

    def to_entity(self, model: ProjectModel) -> Project:
        return Project(
            id_=ProjectId(model.id),
            props=ProjectProps(
                name=ProjectName(model.name),
                description=ProjectDescription(model.description),
                status=ProjectStatus(model.status),
            ),
            created_at_=model.created_at,
            updated_at_=model.updated_at,
        )
```

`src/modules/projects/infrastructure/mappers/__init__.py` :

```python
from .project_mapper import ProjectMapper

__all__ = ["ProjectMapper"]
```

`src/modules/projects/infrastructure/repositories/project_repository.py` :

```python
"""SQLAlchemy repository of projects."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.infrastructure.db.repository import SqlaRepository
from core.infrastructure.db.tracker import AggregateTracker
from modules.projects.domain.entities import Project
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.domain.value_objects import ProjectId, ProjectName
from modules.projects.infrastructure.mappers import ProjectMapper
from modules.projects.infrastructure.models import ProjectModel


class SqlaProjectRepository(
    SqlaRepository[Project, ProjectModel], ProjectRepositoryPort
):
    sortable_fields = frozenset({"name", "created_at", "updated_at"})
    filterable_fields = frozenset({"status"})
    searchable_fields = ("name",)

    def __init__(self, session: AsyncSession, tracker: AggregateTracker) -> None:
        super().__init__(
            session=session, tracker=tracker, model=ProjectModel, mapper=ProjectMapper()
        )

    async def exists_by_name(
        self, name: ProjectName, *, exclude_id: ProjectId | None = None
    ) -> bool:
        statement = select(ProjectModel.id).where(ProjectModel.name == name.value)
        if exclude_id is not None:
            statement = statement.where(ProjectModel.id != exclude_id.value)
        return await self._session.scalar(statement.limit(1)) is not None
```

`src/modules/projects/infrastructure/repositories/__init__.py` :

```python
from .project_repository import SqlaProjectRepository

__all__ = ["SqlaProjectRepository"]
```

`src/modules/projects/provider.py` :

```python
"""Dishka provider of the projects module."""

from dishka import Provider, Scope, provide, provide_all

from modules.projects.application.commands import (
    ArchiveProjectCommand,
    CreateProjectCommand,
    DeleteProjectCommand,
    UpdateProjectCommand,
)
from modules.projects.application.queries import (
    GetProjectByIdQuery,
    ListProjectsQuery,
)
from modules.projects.domain.ports import ProjectRepositoryPort
from modules.projects.infrastructure.repositories import SqlaProjectRepository
from modules.projects.public import ProjectsPublicApi


class ProjectsProvider(Provider):
    scope = Scope.REQUEST

    repository = provide(SqlaProjectRepository, provides=ProjectRepositoryPort)
    use_cases = provide_all(
        CreateProjectCommand,
        UpdateProjectCommand,
        ArchiveProjectCommand,
        DeleteProjectCommand,
        GetProjectByIdQuery,
        ListProjectsQuery,
    )
    public_api = provide(ProjectsPublicApi)
```

`src/app/models.py` (remplacer) :

```python
"""Import every ORM model so that `Base.metadata` describes the whole schema."""

from core.infrastructure.db.base import Base
from modules.projects.infrastructure.models import ProjectModel

__all__ = ["Base", "ProjectModel"]
```

`src/app/providers.py` (remplacer) :

```python
"""Every Dishka provider of the application."""

from dishka import Provider

from app.event_handlers import EventHandlersProvider
from core.infrastructure.provider import core_providers
from modules.projects.provider import ProjectsProvider


def get_providers() -> tuple[Provider, ...]:
    return (*core_providers(), EventHandlersProvider(), ProjectsProvider())
```

- [ ] **Step 4: Écrire la migration initiale**

Supprimer `migrations/versions/.gitkeep`, puis créer `migrations/versions/2026_09_17_1200-0001_initial_schema.py` :

```python
"""Initial schema.

Revision ID: 0001
Revises:
Create Date: 2026-09-17 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('active', 'archived')", name=op.f("ck_projects_status")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
        sa.UniqueConstraint("name", name=op.f("uq_projects_name")),
    )
    op.create_index(op.f("ix_projects_status"), "projects", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_projects_status"), table_name="projects")
    op.drop_table("projects")
```

- [ ] **Step 5: Vérifier le succès**

```bash
uv run pytest tests/integration -v
```

Expected : tous les tests passent, y compris `test_migrations_match_the_orm_models`. Si ce dernier signale une différence, corriger la migration pour qu'elle corresponde au modèle (le modèle fait foi) et relancer.

- [ ] **Step 6: Lint et commit**

```bash
make format && make lint
git add -A migrations src/modules/projects src/app tests/integration/projects
git commit -m "feat(projects): add project persistence and initial migration" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 13: `projects` — API HTTP

**Files:**
- Create: `src/modules/projects/presentation/__init__.py` (vide), `src/modules/projects/presentation/http/__init__.py` (vide), `src/modules/projects/presentation/http/schemas.py`, `src/modules/projects/presentation/http/router.py`, `src/modules/projects/presentation/http/controllers/{__init__,create_project,list_projects,get_project,update_project,archive_project,delete_project}.py`
- Modify: `src/app/routers.py`
- Test: `tests/integration/projects/test_projects_api.py`

**Interfaces:**
- Consumes: use cases `projects` (Task 11), `ProjectsProvider` (Task 12), `error_responses`, `PageResponse`, `to_page_response` (Task 8), fixture `client` (Task 9).
- Produces:
  - `modules.projects.presentation.http.schemas` : `SORT_DESCRIPTION`, `CreateProjectBody(name, description="")`, `UpdateProjectBody(name=None, description=None)` (tous deux `extra="forbid"`), `ProjectResponse(id, name, description, status, created_at, updated_at)`.
  - `modules.projects.presentation.http.router.create_projects_router() -> APIRouter` (tag `Projects`) exposant `POST /projects`, `GET /projects`, `GET /projects/{project_id}`, `PATCH /projects/{project_id}`, `POST /projects/{project_id}/archive`, `DELETE /projects/{project_id}`, monté sous `/api/v1`.

- [ ] **Step 1: Écrire les tests d'intégration qui échouent**

`tests/integration/projects/test_projects_api.py` :

```python
"""Projects HTTP API against PostgreSQL."""

from datetime import datetime
from http import HTTPStatus
from typing import Any, cast
from uuid import uuid4

from httpx import AsyncClient

PROJECTS_URL = "/api/v1/projects"


async def create_project(
    client: AsyncClient, name: str = "Website", description: str = ""
) -> dict[str, Any]:
    response = await client.post(
        PROJECTS_URL, json={"name": name, "description": description}
    )
    assert response.status_code == HTTPStatus.CREATED, response.text
    return cast(dict[str, Any], response.json())


async def test_create_then_get_a_project(client: AsyncClient) -> None:
    created = await create_project(client, name="  Website ", description="Site")

    response = await client.get(f"{PROJECTS_URL}/{created['id']}")

    assert created["name"] == "Website"
    assert created["status"] == "active"
    assert response.status_code == HTTPStatus.OK
    assert response.json() == created


async def test_duplicate_name_is_a_conflict(client: AsyncClient) -> None:
    await create_project(client, name="Website")

    response = await client.post(PROJECTS_URL, json={"name": "Website"})

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()["code"] == "project_name_already_exists"


async def test_blank_name_is_rejected_by_the_domain(client: AsyncClient) -> None:
    response = await client.post(PROJECTS_URL, json={"name": "   "})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert response.json()["code"] == "invalid_project_name"


async def test_malformed_body_is_a_request_validation_error(
    client: AsyncClient,
) -> None:
    response = await client.post(PROJECTS_URL, json={"description": "no name"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert response.json()["code"] == "request_validation_error"


async def test_unknown_project_is_not_found(client: AsyncClient) -> None:
    response = await client.get(f"{PROJECTS_URL}/{uuid4()}")

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["code"] == "project_not_found"


async def test_update_a_project(client: AsyncClient) -> None:
    project = await create_project(client)

    response = await client.patch(
        f"{PROJECTS_URL}/{project['id']}",
        json={"name": "Intranet", "description": "Internal"},
    )

    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert (body["name"], body["description"]) == ("Intranet", "Internal")
    assert datetime.fromisoformat(body["updated_at"]) > datetime.fromisoformat(
        project["updated_at"]
    )


async def test_renaming_to_an_existing_name_is_a_conflict(client: AsyncClient) -> None:
    await create_project(client, name="Website")
    project = await create_project(client, name="Intranet")

    response = await client.patch(
        f"{PROJECTS_URL}/{project['id']}", json={"name": "Website"}
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()["code"] == "project_name_already_exists"


async def test_archive_a_project(client: AsyncClient) -> None:
    project = await create_project(client)
    url = f"{PROJECTS_URL}/{project['id']}"

    archived = await client.post(f"{url}/archive")
    archived_again = await client.post(f"{url}/archive")
    updated = await client.patch(url, json={"name": "Other"})

    assert archived.status_code == HTTPStatus.OK
    assert archived.json()["status"] == "archived"
    assert archived_again.status_code == HTTPStatus.CONFLICT
    assert archived_again.json()["code"] == "project_already_archived"
    assert updated.status_code == HTTPStatus.CONFLICT
    assert updated.json()["code"] == "project_archived"


async def test_delete_a_project(client: AsyncClient) -> None:
    project = await create_project(client)
    url = f"{PROJECTS_URL}/{project['id']}"

    deleted = await client.delete(url)
    fetched = await client.get(url)
    deleted_again = await client.delete(url)

    assert deleted.status_code == HTTPStatus.NO_CONTENT
    assert deleted.content == b""
    assert fetched.status_code == HTTPStatus.NOT_FOUND
    assert deleted_again.status_code == HTTPStatus.NOT_FOUND


async def test_list_projects_filters_sorts_and_paginates(client: AsyncClient) -> None:
    projects = {
        name: await create_project(client, name=name)
        for name in ("Gamma", "Alpha", "Beta")
    }
    await client.post(f"{PROJECTS_URL}/{projects['Beta']['id']}/archive")

    response = await client.get(
        PROJECTS_URL, params={"status": "active", "sort": "name", "size": 1, "page": 2}
    )

    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert [item["name"] for item in body["items"]] == ["Gamma"]
    assert (body["total"], body["page"], body["size"], body["pages"]) == (2, 2, 1, 2)


async def test_list_projects_search_matches_wildcards_literally(
    client: AsyncClient,
) -> None:
    await create_project(client, name="50% off")
    await create_project(client, name="500 offers")

    response = await client.get(PROJECTS_URL, params={"search": "50%"})

    assert [item["name"] for item in response.json()["items"]] == ["50% off"]


async def test_list_projects_rejects_an_unknown_sort_field(client: AsyncClient) -> None:
    response = await client.get(PROJECTS_URL, params={"sort": "-description"})

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert response.json()["code"] == "invalid_sort_field"
```

- [ ] **Step 2: Vérifier l'échec**

Run: `uv run pytest tests/integration/projects/test_projects_api.py -v`
Expected: FAIL (404 sur `/api/v1/projects`).

- [ ] **Step 3: Implémenter les schémas et contrôleurs**

`src/modules/projects/presentation/http/schemas.py` :

```python
"""HTTP models of the projects module."""

from datetime import datetime
from typing import Final
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.projects.domain.enums import ProjectStatus
from modules.projects.domain.value_objects.project_description import (
    MAX_LENGTH as DESCRIPTION_MAX_LENGTH,
)
from modules.projects.domain.value_objects.project_name import (
    MAX_LENGTH as NAME_MAX_LENGTH,
)

SORT_DESCRIPTION: Final[str] = (
    "Field to sort by, prefixed with '-' for descending order. "
    "Allowed: name, created_at, updated_at."
)


class CreateProjectBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)


class UpdateProjectBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=NAME_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)


class ProjectResponse(BaseModel):
    id: UUID
    name: str
    description: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime
```

`src/modules/projects/presentation/http/controllers/create_project.py` :

```python
"""POST /projects."""

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.projects.application.commands import (
    CreateProjectCommand,
    CreateProjectRequest,
)
from modules.projects.presentation.http.schemas import (
    CreateProjectBody,
    ProjectResponse,
)


def create_create_project_router() -> APIRouter:
    router = APIRouter()

    @router.post(
        "/projects",
        status_code=HTTPStatus.CREATED,
        response_model=ProjectResponse,
        responses=error_responses(HTTPStatus.CONFLICT, HTTPStatus.UNPROCESSABLE_CONTENT),
        summary="Create a project",
    )
    @inject
    async def create_project(
        body: CreateProjectBody, command: FromDishka[CreateProjectCommand]
    ) -> ProjectResponse:
        project = await command.execute(
            CreateProjectRequest(name=body.name, description=body.description)
        )
        return ProjectResponse.model_validate(project, from_attributes=True)

    return router
```

`src/modules/projects/presentation/http/controllers/list_projects.py` :

```python
"""GET /projects."""

from http import HTTPStatus
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query

from core.domain.pagination import MAX_PAGE_SIZE
from core.presentation.http.errors import error_responses
from core.presentation.http.pagination import PageResponse, to_page_response
from modules.projects.application.queries import (
    ListProjectsQuery,
    ListProjectsRequest,
)
from modules.projects.domain.enums import ProjectStatus
from modules.projects.presentation.http.schemas import (
    SORT_DESCRIPTION,
    ProjectResponse,
)


def create_list_projects_router() -> APIRouter:
    router = APIRouter()

    @router.get(
        "/projects",
        response_model=PageResponse[ProjectResponse],
        responses=error_responses(HTTPStatus.UNPROCESSABLE_CONTENT),
        summary="List projects",
    )
    @inject
    async def list_projects(
        query: FromDishka[ListProjectsQuery],
        page: Annotated[int, Query(ge=1)] = 1,
        size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 20,
        status: Annotated[ProjectStatus | None, Query()] = None,
        search: Annotated[str | None, Query(min_length=1, max_length=100)] = None,
        sort: Annotated[str, Query(description=SORT_DESCRIPTION)] = "-created_at",
    ) -> PageResponse[ProjectResponse]:
        result = await query.execute(
            ListProjectsRequest(
                page=page, size=size, status=status, search=search, sort=sort
            )
        )
        return to_page_response(result, ProjectResponse)

    return router
```

`src/modules/projects/presentation/http/controllers/get_project.py` :

```python
"""GET /projects/{project_id}."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.projects.application.queries import (
    GetProjectByIdQuery,
    GetProjectByIdRequest,
)
from modules.projects.presentation.http.schemas import ProjectResponse


def create_get_project_router() -> APIRouter:
    router = APIRouter()

    @router.get(
        "/projects/{project_id}",
        response_model=ProjectResponse,
        responses=error_responses(HTTPStatus.NOT_FOUND),
        summary="Get a project",
    )
    @inject
    async def get_project(
        project_id: UUID, query: FromDishka[GetProjectByIdQuery]
    ) -> ProjectResponse:
        project = await query.execute(GetProjectByIdRequest(project_id=project_id))
        return ProjectResponse.model_validate(project, from_attributes=True)

    return router
```

`src/modules/projects/presentation/http/controllers/update_project.py` :

```python
"""PATCH /projects/{project_id}."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.projects.application.commands import (
    UpdateProjectCommand,
    UpdateProjectRequest,
)
from modules.projects.presentation.http.schemas import (
    ProjectResponse,
    UpdateProjectBody,
)


def create_update_project_router() -> APIRouter:
    router = APIRouter()

    @router.patch(
        "/projects/{project_id}",
        response_model=ProjectResponse,
        responses=error_responses(
            HTTPStatus.NOT_FOUND, HTTPStatus.CONFLICT, HTTPStatus.UNPROCESSABLE_CONTENT
        ),
        summary="Update a project",
    )
    @inject
    async def update_project(
        project_id: UUID,
        body: UpdateProjectBody,
        command: FromDishka[UpdateProjectCommand],
    ) -> ProjectResponse:
        project = await command.execute(
            UpdateProjectRequest(
                project_id=project_id, name=body.name, description=body.description
            )
        )
        return ProjectResponse.model_validate(project, from_attributes=True)

    return router
```

`src/modules/projects/presentation/http/controllers/archive_project.py` :

```python
"""POST /projects/{project_id}/archive."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.projects.application.commands import (
    ArchiveProjectCommand,
    ArchiveProjectRequest,
)
from modules.projects.presentation.http.schemas import ProjectResponse


def create_archive_project_router() -> APIRouter:
    router = APIRouter()

    @router.post(
        "/projects/{project_id}/archive",
        response_model=ProjectResponse,
        responses=error_responses(HTTPStatus.NOT_FOUND, HTTPStatus.CONFLICT),
        summary="Archive a project",
    )
    @inject
    async def archive_project(
        project_id: UUID, command: FromDishka[ArchiveProjectCommand]
    ) -> ProjectResponse:
        project = await command.execute(ArchiveProjectRequest(project_id=project_id))
        return ProjectResponse.model_validate(project, from_attributes=True)

    return router
```

`src/modules/projects/presentation/http/controllers/delete_project.py` :

```python
"""DELETE /projects/{project_id}."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.projects.application.commands import (
    DeleteProjectCommand,
    DeleteProjectRequest,
)


def create_delete_project_router() -> APIRouter:
    router = APIRouter()

    @router.delete(
        "/projects/{project_id}",
        status_code=HTTPStatus.NO_CONTENT,
        responses=error_responses(HTTPStatus.NOT_FOUND),
        summary="Delete a project",
    )
    @inject
    async def delete_project(
        project_id: UUID, command: FromDishka[DeleteProjectCommand]
    ) -> None:
        await command.execute(DeleteProjectRequest(project_id=project_id))

    return router
```

`src/modules/projects/presentation/http/controllers/__init__.py` :

```python
from .archive_project import create_archive_project_router
from .create_project import create_create_project_router
from .delete_project import create_delete_project_router
from .get_project import create_get_project_router
from .list_projects import create_list_projects_router
from .update_project import create_update_project_router

__all__ = [
    "create_archive_project_router",
    "create_create_project_router",
    "create_delete_project_router",
    "create_get_project_router",
    "create_list_projects_router",
    "create_update_project_router",
]
```

`src/modules/projects/presentation/http/router.py` :

```python
"""HTTP router of the projects module."""

from fastapi import APIRouter

from modules.projects.presentation.http.controllers import (
    create_archive_project_router,
    create_create_project_router,
    create_delete_project_router,
    create_get_project_router,
    create_list_projects_router,
    create_update_project_router,
)


def create_projects_router() -> APIRouter:
    router = APIRouter(tags=["Projects"])
    for sub_router in (
        create_create_project_router(),
        create_list_projects_router(),
        create_get_project_router(),
        create_update_project_router(),
        create_archive_project_router(),
        create_delete_project_router(),
    ):
        router.include_router(sub_router)
    return router
```

Dans `src/app/routers.py`, remplacer `create_api_v1_router` et ajouter l'import :

```python
from modules.projects.presentation.http.router import create_projects_router


def create_api_v1_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.include_router(create_projects_router())
    return router
```

- [ ] **Step 4: Vérifier le succès**

Run: `uv run pytest -v`
Expected: tous les tests (unitaires et intégration) passent.

- [ ] **Step 5: Lint et commit**

```bash
make format && make lint
git add src/modules/projects src/app tests/integration/projects
git commit -m "feat(projects): expose the projects HTTP API" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 14: `tasks` — domaine

**Files:**
- Create (vides) : `src/modules/tasks/domain/__init__.py`
- Create: `src/modules/tasks/__init__.py`, `src/modules/tasks/domain/enums.py`, `src/modules/tasks/domain/errors.py`, `src/modules/tasks/domain/value_objects/{__init__,task_id,task_title,task_description}.py`, `src/modules/tasks/domain/entities/{__init__,task}.py`, `src/modules/tasks/domain/ports/{__init__,task_repository,project_lookup}.py`
- Test: `tests/unit/tasks/__init__.py` (vide), `tests/unit/tasks/factories.py`, `tests/unit/tasks/test_task_domain.py`

**Interfaces:**
- Consumes: briques du domaine (Task 3), pagination (Task 4).
- Produces:
  - `modules.tasks.domain.enums.TaskStatus(StrEnum)` : `TODO="todo"`, `IN_PROGRESS="in_progress"`, `DONE="done"`, `CANCELLED="cancelled"` ; propriété `is_terminal` (DONE, CANCELLED).
  - `modules.tasks.domain.errors` : `TaskNotFoundError(task_id)` (`task_not_found`), `TaskClosedError(task_id, status)` (`task_closed`), `InvalidTaskTransitionError(task_id, *, current, target)` (`invalid_task_transition`, `details` = `task_id`, `current`, `target`), `TaskProjectNotFoundError(project_id)` (`task_project_not_found`), `TaskProjectArchivedError(project_id)` (`task_project_archived`).
  - `modules.tasks.domain.value_objects` : `TaskId(EntityId)` ; `TaskTitle(value)` (strip, 1..200, `invalid_task_title`, constantes `MIN_LENGTH`/`MAX_LENGTH`) ; `TaskDescription(value)` (strip, ≤ 5000, `invalid_task_description`, constante `MAX_LENGTH`).
  - `modules.tasks.domain.entities` : `ALLOWED_TRANSITIONS: Mapping[TaskStatus, frozenset[TaskStatus]]` ; `TaskProps(project_id: UUID, title, description, status)` ; `Task(AggregateRoot[TaskId, TaskProps])` avec `create(*, project_id, title, description="")`, `rename(title)`, `change_description(description)`, `start()`, `complete()`, `cancel()`, `change_status(target)`.
  - `modules.tasks.domain.ports` : `TaskRepositoryPort` (`add`, `save`, `delete`, `get_by_id(entity_id: TaskId)`, `list_page`, `list_open_by_project(project_id: UUID) -> list[Task]`, `delete_by_project(project_id: UUID) -> None`) ; `ProjectRef(id: UUID, is_active: bool)` ; `ProjectLookupPort` (`get(project_id: UUID) -> ProjectRef | None`).
  - Tests : `tests.unit.tasks.factories` expose `PAST` et `make_task(*, project_id=None, title="Write copy", status=TaskStatus.TODO) -> Task`.

- [ ] **Step 1: Écrire les tests qui échouent**

`tests/unit/tasks/factories.py` :

```python
"""Builders of task aggregates for tests."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from modules.tasks.domain.entities import Task, TaskProps
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.value_objects import TaskDescription, TaskId, TaskTitle

PAST = datetime(2000, 1, 1, tzinfo=UTC)


def make_task(
    *,
    project_id: UUID | None = None,
    title: str = "Write copy",
    status: TaskStatus = TaskStatus.TODO,
) -> Task:
    """A task as loaded from storage: no pending event, timestamps in the past."""
    return Task(
        id_=TaskId.generate(),
        props=TaskProps(
            project_id=project_id or uuid4(),
            title=TaskTitle(title),
            description=TaskDescription(""),
            status=status,
        ),
        created_at_=PAST,
        updated_at_=PAST,
    )
```

`tests/unit/tasks/test_task_domain.py` :

```python
"""Value objects and lifecycle of the task aggregate."""

from collections.abc import Callable
from uuid import uuid4

import pytest

from core.domain.errors import DomainValidationError
from modules.tasks.domain.entities import Task
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.errors import InvalidTaskTransitionError, TaskClosedError
from modules.tasks.domain.value_objects import TaskDescription, TaskTitle
from modules.tasks.domain.value_objects.task_description import (
    MAX_LENGTH as DESCRIPTION_MAX_LENGTH,
)
from modules.tasks.domain.value_objects.task_title import (
    MAX_LENGTH as TITLE_MAX_LENGTH,
)
from tests.unit.tasks.factories import PAST, make_task

TODO, IN_PROGRESS = TaskStatus.TODO, TaskStatus.IN_PROGRESS
DONE, CANCELLED = TaskStatus.DONE, TaskStatus.CANCELLED


class TestValueObjects:
    def test_title_is_stripped(self) -> None:
        assert TaskTitle("  Write copy ").value == "Write copy"

    @pytest.mark.parametrize("raw", ["", "  ", "x" * (TITLE_MAX_LENGTH + 1)])
    def test_title_length_is_validated(self, raw: str) -> None:
        with pytest.raises(DomainValidationError) as exc_info:
            TaskTitle(raw)

        assert exc_info.value.code == "invalid_task_title"

    def test_description_length_is_validated(self) -> None:
        with pytest.raises(DomainValidationError) as exc_info:
            TaskDescription("x" * (DESCRIPTION_MAX_LENGTH + 1))

        assert exc_info.value.code == "invalid_task_description"


class TestTaskStatus:
    @pytest.mark.parametrize(
        ("status", "terminal"),
        [(TODO, False), (IN_PROGRESS, False), (DONE, True), (CANCELLED, True)],
    )
    def test_is_terminal(self, status: TaskStatus, terminal: bool) -> None:
        assert status.is_terminal is terminal


class TestTaskCreation:
    def test_create_builds_a_todo_task(self) -> None:
        project_id = uuid4()

        task = Task.create(project_id=project_id, title=" Draft ", description="Text")

        assert task.props.project_id == project_id
        assert task.props.title == TaskTitle("Draft")
        assert task.props.description == TaskDescription("Text")
        assert task.props.status is TODO


class TestTaskLifecycle:
    @pytest.mark.parametrize(
        ("current", "target"),
        [
            (TODO, IN_PROGRESS),
            (TODO, DONE),
            (TODO, CANCELLED),
            (IN_PROGRESS, DONE),
            (IN_PROGRESS, CANCELLED),
        ],
    )
    def test_allowed_transitions(self, current: TaskStatus, target: TaskStatus) -> None:
        task = make_task(status=current)

        task.change_status(target)

        assert task.props.status is target
        assert task.updated_at_ > PAST

    @pytest.mark.parametrize(
        ("current", "target"),
        [
            (TODO, TODO),
            (IN_PROGRESS, TODO),
            (IN_PROGRESS, IN_PROGRESS),
            (DONE, TODO),
            (DONE, CANCELLED),
            (CANCELLED, DONE),
            (CANCELLED, IN_PROGRESS),
        ],
    )
    def test_forbidden_transitions(self, current: TaskStatus, target: TaskStatus) -> None:
        task = make_task(status=current)

        with pytest.raises(InvalidTaskTransitionError) as exc_info:
            task.change_status(target)

        assert exc_info.value.details == {
            "task_id": str(task.id_.value),
            "current": current.value,
            "target": target.value,
        }
        assert task.props.status is current

    @pytest.mark.parametrize(
        ("action", "expected"),
        [
            (Task.start, IN_PROGRESS),
            (Task.complete, DONE),
            (Task.cancel, CANCELLED),
        ],
    )
    def test_shortcuts(
        self, action: Callable[[Task], None], expected: TaskStatus
    ) -> None:
        task = make_task()

        action(task)

        assert task.props.status is expected


class TestTaskChanges:
    def test_rename_and_change_description(self) -> None:
        task = make_task()

        task.rename("New title")
        task.change_description("New description")

        assert task.props.title == TaskTitle("New title")
        assert task.props.description == TaskDescription("New description")
        assert task.updated_at_ > PAST

    @pytest.mark.parametrize("status", [DONE, CANCELLED])
    @pytest.mark.parametrize(
        "change",
        [
            lambda task: task.rename("Other"),
            lambda task: task.change_description("Other"),
        ],
    )
    def test_closed_task_cannot_be_modified(
        self, status: TaskStatus, change: Callable[[Task], None]
    ) -> None:
        task = make_task(status=status)

        with pytest.raises(TaskClosedError):
            change(task)
```

- [ ] **Step 2: Vérifier l'échec**

Run: `uv run pytest tests/unit/tasks -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'modules.tasks'`).

- [ ] **Step 3: Implémenter**

`src/modules/tasks/__init__.py` :

```python
"""Tasks module: units of work that belong to a project."""
```

`src/modules/tasks/domain/enums.py` :

```python
"""Enumerations of the tasks module."""

from enum import StrEnum


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self in {TaskStatus.DONE, TaskStatus.CANCELLED}
```

`src/modules/tasks/domain/errors.py` :

```python
"""Business errors of the tasks module."""

from uuid import UUID

from core.domain.errors import BusinessRuleViolationError, NotFoundError
from modules.tasks.domain.enums import TaskStatus


class TaskNotFoundError(NotFoundError):
    def __init__(self, task_id: UUID) -> None:
        super().__init__(
            f"Task '{task_id}' was not found.",
            code="task_not_found",
            details={"task_id": str(task_id)},
        )


class TaskClosedError(BusinessRuleViolationError):
    def __init__(self, task_id: UUID, status: TaskStatus) -> None:
        super().__init__(
            f"Task '{task_id}' is {status} and can no longer be modified.",
            code="task_closed",
            details={"task_id": str(task_id), "status": status.value},
        )


class InvalidTaskTransitionError(BusinessRuleViolationError):
    def __init__(
        self, task_id: UUID, *, current: TaskStatus, target: TaskStatus
    ) -> None:
        super().__init__(
            f"Task '{task_id}' cannot move from {current} to {target}.",
            code="invalid_task_transition",
            details={
                "task_id": str(task_id),
                "current": current.value,
                "target": target.value,
            },
        )


class TaskProjectNotFoundError(NotFoundError):
    def __init__(self, project_id: UUID) -> None:
        super().__init__(
            f"Project '{project_id}' was not found.",
            code="task_project_not_found",
            details={"project_id": str(project_id)},
        )


class TaskProjectArchivedError(BusinessRuleViolationError):
    def __init__(self, project_id: UUID) -> None:
        super().__init__(
            f"Project '{project_id}' is archived: no task can be added to it.",
            code="task_project_archived",
            details={"project_id": str(project_id)},
        )
```

`src/modules/tasks/domain/value_objects/task_id.py` :

```python
"""Task identifier."""

from dataclasses import dataclass

from core.domain.identifier import EntityId


@dataclass(frozen=True, slots=True, repr=False)
class TaskId(EntityId):
    """Identity of a task."""
```

`src/modules/tasks/domain/value_objects/task_title.py` :

```python
"""Task title."""

from dataclasses import dataclass
from typing import Final

from core.domain.errors import DomainValidationError
from core.domain.value_object import ValueObject

MIN_LENGTH: Final[int] = 1
MAX_LENGTH: Final[int] = 200


@dataclass(frozen=True, slots=True, repr=False)
class TaskTitle(ValueObject):
    """Short summary of the task; surrounding whitespace is removed."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not MIN_LENGTH <= len(normalized) <= MAX_LENGTH:
            raise DomainValidationError(
                f"Task title must be {MIN_LENGTH} to {MAX_LENGTH} characters long.",
                code="invalid_task_title",
                details={"min_length": MIN_LENGTH, "max_length": MAX_LENGTH},
            )
        object.__setattr__(self, "value", normalized)
```

`src/modules/tasks/domain/value_objects/task_description.py` :

```python
"""Task description."""

from dataclasses import dataclass
from typing import Final

from core.domain.errors import DomainValidationError
from core.domain.value_object import ValueObject

MAX_LENGTH: Final[int] = 5000


@dataclass(frozen=True, slots=True, repr=False)
class TaskDescription(ValueObject):
    """Free text, possibly empty; surrounding whitespace is removed."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if len(normalized) > MAX_LENGTH:
            raise DomainValidationError(
                f"Task description cannot exceed {MAX_LENGTH} characters.",
                code="invalid_task_description",
                details={"max_length": MAX_LENGTH},
            )
        object.__setattr__(self, "value", normalized)
```

`src/modules/tasks/domain/value_objects/__init__.py` :

```python
from .task_description import TaskDescription
from .task_id import TaskId
from .task_title import TaskTitle

__all__ = ["TaskDescription", "TaskId", "TaskTitle"]
```

`src/modules/tasks/domain/entities/task.py` :

```python
"""Task aggregate."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Self
from uuid import UUID

from core.domain.aggregate_root import AggregateRoot
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.errors import InvalidTaskTransitionError, TaskClosedError
from modules.tasks.domain.value_objects import TaskDescription, TaskId, TaskTitle

ALLOWED_TRANSITIONS: Final[Mapping[TaskStatus, frozenset[TaskStatus]]] = (
    MappingProxyType({
        TaskStatus.TODO: frozenset({
            TaskStatus.IN_PROGRESS,
            TaskStatus.DONE,
            TaskStatus.CANCELLED,
        }),
        TaskStatus.IN_PROGRESS: frozenset({TaskStatus.DONE, TaskStatus.CANCELLED}),
        TaskStatus.DONE: frozenset(),
        TaskStatus.CANCELLED: frozenset(),
    })
)


@dataclass(slots=True)
class TaskProps:
    project_id: UUID
    title: TaskTitle
    description: TaskDescription
    status: TaskStatus


class Task(AggregateRoot[TaskId, TaskProps]):
    """
    A unit of work that belongs to a project.

    Lifecycle: todo → in_progress → done, and any open task can be cancelled.
    Done and cancelled tasks are closed: they can no longer change.
    """

    @classmethod
    def create(cls, *, project_id: UUID, title: str, description: str = "") -> Self:
        return cls(
            id_=TaskId.generate(),
            props=TaskProps(
                project_id=project_id,
                title=TaskTitle(title),
                description=TaskDescription(description),
                status=TaskStatus.TODO,
            ),
        )

    def rename(self, title: str) -> None:
        self._ensure_open()
        self.props.title = TaskTitle(title)
        self.touch()

    def change_description(self, description: str) -> None:
        self._ensure_open()
        self.props.description = TaskDescription(description)
        self.touch()

    def start(self) -> None:
        self.change_status(TaskStatus.IN_PROGRESS)

    def complete(self) -> None:
        self.change_status(TaskStatus.DONE)

    def cancel(self) -> None:
        self.change_status(TaskStatus.CANCELLED)

    def change_status(self, target: TaskStatus) -> None:
        current = self.props.status
        if target not in ALLOWED_TRANSITIONS[current]:
            raise InvalidTaskTransitionError(
                self.id_.value, current=current, target=target
            )
        self.props.status = target
        self.touch()

    def validate(self) -> None:
        """Invariants are enforced by the value objects."""

    def _ensure_open(self) -> None:
        if self.props.status.is_terminal:
            raise TaskClosedError(self.id_.value, self.props.status)
```

`src/modules/tasks/domain/entities/__init__.py` :

```python
from .task import ALLOWED_TRANSITIONS, Task, TaskProps

__all__ = ["ALLOWED_TRANSITIONS", "Task", "TaskProps"]
```

`src/modules/tasks/domain/ports/task_repository.py` :

```python
"""Persistence port of the task aggregate."""

from collections.abc import Mapping
from typing import Protocol
from uuid import UUID

from core.domain.pagination import Page, PageParams, Sort
from modules.tasks.domain.entities import Task
from modules.tasks.domain.value_objects import TaskId


class TaskRepositoryPort(Protocol):
    async def add(self, entity: Task) -> None: ...

    async def save(self, entity: Task) -> None: ...

    async def delete(self, entity: Task) -> None: ...

    async def get_by_id(self, entity_id: TaskId) -> Task | None: ...

    async def list_page(
        self,
        params: PageParams,
        *,
        sort: Sort | None = None,
        filters: Mapping[str, object] | None = None,
        search: str | None = None,
    ) -> Page[Task]: ...

    async def list_open_by_project(self, project_id: UUID) -> list[Task]: ...

    async def delete_by_project(self, project_id: UUID) -> None: ...
```

`src/modules/tasks/domain/ports/project_lookup.py` :

```python
"""What the tasks module needs to know about projects (owned by `tasks`)."""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectRef:
    id: UUID
    is_active: bool


class ProjectLookupPort(Protocol):
    async def get(self, project_id: UUID) -> ProjectRef | None: ...
```

`src/modules/tasks/domain/ports/__init__.py` :

```python
from .project_lookup import ProjectLookupPort, ProjectRef
from .task_repository import TaskRepositoryPort

__all__ = ["ProjectLookupPort", "ProjectRef", "TaskRepositoryPort"]
```

- [ ] **Step 4: Vérifier le succès**

Run: `uv run pytest tests/unit/tasks -v`
Expected: tous les tests passent.

- [ ] **Step 5: Lint et commit**

```bash
make format && make lint
git add src/modules/tasks tests/unit/tasks
git commit -m "feat(tasks): add task domain model and lifecycle" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 15: `tasks` — use cases et handlers d'événements

**Files:**
- Create: `src/modules/tasks/application/__init__.py` (vide), `src/modules/tasks/application/dto.py`, `src/modules/tasks/application/commands/{__init__,create_task,update_task,change_task_status,delete_task}.py`, `src/modules/tasks/application/queries/{__init__,get_task_by_id,list_tasks}.py`, `src/modules/tasks/application/event_handlers/{__init__,cancel_tasks_on_project_archived,delete_tasks_on_project_deleted}.py`
- Test: `tests/fakes/tasks.py`, `tests/unit/tasks/test_task_use_cases.py`

**Interfaces:**
- Consumes: domaine `tasks` (Task 14), `UnitOfWork`, `EventHandler` (Task 4), `ProjectArchived`, `ProjectDeleted` depuis `modules.projects.public` (Task 11), `FakeUnitOfWork` (Task 11).
- Produces:
  - `modules.tasks.application.dto.TaskDTO(id, project_id, title, description, status, created_at, updated_at)` avec `from_entity(task)`.
  - Commandes : `CreateTaskCommand(repository: TaskRepositoryPort, project_lookup: ProjectLookupPort, uow: UnitOfWork)` + `CreateTaskRequest(project_id, title, description="")` → `TaskDTO` ; `UpdateTaskCommand(repository, uow)` + `UpdateTaskRequest(task_id, title=None, description=None)` → `TaskDTO` ; `ChangeTaskStatusCommand(repository, uow)` + `ChangeTaskStatusRequest(task_id, status)` → `TaskDTO` ; `DeleteTaskCommand(repository, uow)` + `DeleteTaskRequest(task_id)` → `None`.
  - Requêtes : `GetTaskByIdQuery(repository)` + `GetTaskByIdRequest(task_id)` → `TaskDTO` ; `ListTasksQuery(repository)` + `ListTasksRequest(page=1, size=20, project_id=None, status=None, sort="-created_at")` → `Page[TaskDTO]`.
  - Handlers : `CancelTasksOnProjectArchived(repository: TaskRepositoryPort)` implémente `EventHandler[ProjectArchived]` ; `DeleteTasksOnProjectDeleted(repository: TaskRepositoryPort)` implémente `EventHandler[ProjectDeleted]`.
  - Doublures : `tests.fakes.tasks.InMemoryTaskRepository(*tasks)` (`tasks: dict[UUID, Task]`, `list_calls`) et `FakeProjectLookup(*projects: ProjectRef)`.

- [ ] **Step 1: Écrire les doublures et les tests qui échouent**

`tests/fakes/tasks.py` :

```python
"""In-memory doubles of the tasks module."""

from collections.abc import Mapping
from uuid import UUID

from core.domain.pagination import Page, PageParams, Sort
from modules.tasks.domain.entities import Task
from modules.tasks.domain.ports import (
    ProjectLookupPort,
    ProjectRef,
    TaskRepositoryPort,
)
from modules.tasks.domain.value_objects import TaskId


class InMemoryTaskRepository(TaskRepositoryPort):
    """Dictionary-backed repository; `list_page` records its arguments, never sorts."""

    def __init__(self, *tasks: Task) -> None:
        self.tasks: dict[UUID, Task] = {task.id_.value: task for task in tasks}
        self.list_calls: list[dict[str, object]] = []

    async def add(self, entity: Task) -> None:
        self.tasks[entity.id_.value] = entity

    async def save(self, entity: Task) -> None:
        self.tasks[entity.id_.value] = entity

    async def delete(self, entity: Task) -> None:
        self.tasks.pop(entity.id_.value, None)

    async def get_by_id(self, entity_id: TaskId) -> Task | None:
        return self.tasks.get(entity_id.value)

    async def list_page(
        self,
        params: PageParams,
        *,
        sort: Sort | None = None,
        filters: Mapping[str, object] | None = None,
        search: str | None = None,
    ) -> Page[Task]:
        self.list_calls.append(
            {"params": params, "sort": sort, "filters": filters, "search": search}
        )
        tasks = list(self.tasks.values())
        return Page(
            items=tasks[params.offset : params.offset + params.size],
            total=len(tasks),
            page=params.page,
            size=params.size,
        )

    async def list_open_by_project(self, project_id: UUID) -> list[Task]:
        return [
            task
            for task in self.tasks.values()
            if task.props.project_id == project_id and not task.props.status.is_terminal
        ]

    async def delete_by_project(self, project_id: UUID) -> None:
        self.tasks = {
            key: task
            for key, task in self.tasks.items()
            if task.props.project_id != project_id
        }


class FakeProjectLookup(ProjectLookupPort):
    def __init__(self, *projects: ProjectRef) -> None:
        self.projects = {project.id: project for project in projects}

    async def get(self, project_id: UUID) -> ProjectRef | None:
        return self.projects.get(project_id)
```

`tests/unit/tasks/test_task_use_cases.py` :

```python
"""Commands, queries and event handlers of the tasks module."""

from uuid import uuid4

import pytest

from core.domain.errors import DomainValidationError
from core.domain.pagination import PageParams, Sort, SortDirection
from modules.projects.public import ProjectArchived, ProjectDeleted
from modules.tasks.application.commands import (
    ChangeTaskStatusCommand,
    ChangeTaskStatusRequest,
    CreateTaskCommand,
    CreateTaskRequest,
    DeleteTaskCommand,
    DeleteTaskRequest,
    UpdateTaskCommand,
    UpdateTaskRequest,
)
from modules.tasks.application.dto import TaskDTO
from modules.tasks.application.event_handlers import (
    CancelTasksOnProjectArchived,
    DeleteTasksOnProjectDeleted,
)
from modules.tasks.application.queries import (
    GetTaskByIdQuery,
    GetTaskByIdRequest,
    ListTasksQuery,
    ListTasksRequest,
)
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.errors import (
    InvalidTaskTransitionError,
    TaskClosedError,
    TaskNotFoundError,
    TaskProjectArchivedError,
    TaskProjectNotFoundError,
)
from modules.tasks.domain.ports import ProjectRef
from tests.fakes.tasks import FakeProjectLookup, InMemoryTaskRepository
from tests.fakes.unit_of_work import FakeUnitOfWork
from tests.unit.tasks.factories import make_task


@pytest.fixture
def uow() -> FakeUnitOfWork:
    return FakeUnitOfWork()


class TestCreateTask:
    async def test_creates_a_task_in_an_active_project(
        self, uow: FakeUnitOfWork
    ) -> None:
        project = ProjectRef(id=uuid4(), is_active=True)
        repository = InMemoryTaskRepository()
        command = CreateTaskCommand(repository, FakeProjectLookup(project), uow)

        task = await command.execute(
            CreateTaskRequest(project_id=project.id, title=" Draft ")
        )

        assert (task.project_id, task.title, task.status) == (
            project.id,
            "Draft",
            TaskStatus.TODO,
        )
        assert task.id in repository.tasks
        assert uow.commits == 1

    async def test_unknown_project_is_rejected(self, uow: FakeUnitOfWork) -> None:
        repository = InMemoryTaskRepository()
        command = CreateTaskCommand(repository, FakeProjectLookup(), uow)

        with pytest.raises(TaskProjectNotFoundError):
            await command.execute(CreateTaskRequest(project_id=uuid4(), title="Draft"))

        assert repository.tasks == {}
        assert uow.commits == 0

    async def test_archived_project_is_rejected(self, uow: FakeUnitOfWork) -> None:
        project = ProjectRef(id=uuid4(), is_active=False)
        repository = InMemoryTaskRepository()
        command = CreateTaskCommand(repository, FakeProjectLookup(project), uow)

        with pytest.raises(TaskProjectArchivedError):
            await command.execute(CreateTaskRequest(project_id=project.id, title="x"))

        assert repository.tasks == {}

    async def test_invalid_title_is_rejected(self, uow: FakeUnitOfWork) -> None:
        project = ProjectRef(id=uuid4(), is_active=True)
        command = CreateTaskCommand(
            InMemoryTaskRepository(), FakeProjectLookup(project), uow
        )

        with pytest.raises(DomainValidationError):
            await command.execute(CreateTaskRequest(project_id=project.id, title=" "))


class TestUpdateTask:
    async def test_updates_title_and_description(self, uow: FakeUnitOfWork) -> None:
        task = make_task()

        result = await UpdateTaskCommand(InMemoryTaskRepository(task), uow).execute(
            UpdateTaskRequest(
                task_id=task.id_.value, title="New title", description="Details"
            )
        )

        assert (result.title, result.description) == ("New title", "Details")
        assert uow.commits == 1

    async def test_closed_task_cannot_be_updated(self, uow: FakeUnitOfWork) -> None:
        task = make_task(status=TaskStatus.DONE)

        with pytest.raises(TaskClosedError):
            await UpdateTaskCommand(InMemoryTaskRepository(task), uow).execute(
                UpdateTaskRequest(task_id=task.id_.value, title="Other")
            )

    async def test_unknown_task(self, uow: FakeUnitOfWork) -> None:
        with pytest.raises(TaskNotFoundError):
            await UpdateTaskCommand(InMemoryTaskRepository(), uow).execute(
                UpdateTaskRequest(task_id=uuid4(), title="Other")
            )


class TestChangeTaskStatus:
    async def test_moves_the_task(self, uow: FakeUnitOfWork) -> None:
        task = make_task()

        result = await ChangeTaskStatusCommand(
            InMemoryTaskRepository(task), uow
        ).execute(
            ChangeTaskStatusRequest(task_id=task.id_.value, status=TaskStatus.DONE)
        )

        assert result.status is TaskStatus.DONE
        assert uow.commits == 1

    async def test_invalid_transition(self, uow: FakeUnitOfWork) -> None:
        task = make_task(status=TaskStatus.DONE)

        with pytest.raises(InvalidTaskTransitionError):
            await ChangeTaskStatusCommand(InMemoryTaskRepository(task), uow).execute(
                ChangeTaskStatusRequest(task_id=task.id_.value, status=TaskStatus.TODO)
            )

        assert uow.commits == 0

    async def test_unknown_task(self, uow: FakeUnitOfWork) -> None:
        with pytest.raises(TaskNotFoundError):
            await ChangeTaskStatusCommand(InMemoryTaskRepository(), uow).execute(
                ChangeTaskStatusRequest(task_id=uuid4(), status=TaskStatus.DONE)
            )


class TestDeleteTask:
    async def test_deletes_the_task(self, uow: FakeUnitOfWork) -> None:
        task = make_task()
        repository = InMemoryTaskRepository(task)

        await DeleteTaskCommand(repository, uow).execute(
            DeleteTaskRequest(task_id=task.id_.value)
        )

        assert repository.tasks == {}
        assert uow.commits == 1

    async def test_unknown_task(self, uow: FakeUnitOfWork) -> None:
        with pytest.raises(TaskNotFoundError):
            await DeleteTaskCommand(InMemoryTaskRepository(), uow).execute(
                DeleteTaskRequest(task_id=uuid4())
            )


class TestTaskQueries:
    async def test_get_by_id(self) -> None:
        task = make_task()

        result = await GetTaskByIdQuery(InMemoryTaskRepository(task)).execute(
            GetTaskByIdRequest(task_id=task.id_.value)
        )

        assert result == TaskDTO.from_entity(task)

    async def test_get_unknown_task(self) -> None:
        with pytest.raises(TaskNotFoundError):
            await GetTaskByIdQuery(InMemoryTaskRepository()).execute(
                GetTaskByIdRequest(task_id=uuid4())
            )

    async def test_list_translates_the_request_for_the_repository(self) -> None:
        project_id = uuid4()
        repository = InMemoryTaskRepository(make_task(), make_task())

        page = await ListTasksQuery(repository).execute(
            ListTasksRequest(
                page=1,
                size=10,
                project_id=project_id,
                status=TaskStatus.TODO,
                sort="title",
            )
        )

        assert repository.list_calls == [
            {
                "params": PageParams(page=1, size=10),
                "sort": Sort("title", SortDirection.ASC),
                "filters": {"project_id": project_id, "status": "todo"},
                "search": None,
            }
        ]
        assert page.total == 2
        assert all(isinstance(item, TaskDTO) for item in page.items)


class TestEventHandlers:
    async def test_archived_project_cancels_only_its_open_tasks(self) -> None:
        project_id = uuid4()
        todo = make_task(project_id=project_id)
        started = make_task(project_id=project_id, status=TaskStatus.IN_PROGRESS)
        done = make_task(project_id=project_id, status=TaskStatus.DONE)
        other_project_task = make_task()
        repository = InMemoryTaskRepository(todo, started, done, other_project_task)

        await CancelTasksOnProjectArchived(repository).handle(
            ProjectArchived(project_id=project_id)
        )

        assert todo.props.status is TaskStatus.CANCELLED
        assert started.props.status is TaskStatus.CANCELLED
        assert done.props.status is TaskStatus.DONE
        assert other_project_task.props.status is TaskStatus.TODO

    async def test_deleted_project_removes_only_its_tasks(self) -> None:
        project_id = uuid4()
        other_project_task = make_task()
        repository = InMemoryTaskRepository(
            make_task(project_id=project_id),
            make_task(project_id=project_id, status=TaskStatus.DONE),
            other_project_task,
        )

        await DeleteTasksOnProjectDeleted(repository).handle(
            ProjectDeleted(project_id=project_id)
        )

        assert list(repository.tasks) == [other_project_task.id_.value]
```

- [ ] **Step 2: Vérifier l'échec**

Run: `uv run pytest tests/unit/tasks/test_task_use_cases.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'modules.tasks.application'`).

- [ ] **Step 3: Implémenter la couche application**

`src/modules/tasks/application/dto.py` :

```python
"""Data returned by the use cases of the tasks module."""

from dataclasses import dataclass
from datetime import datetime
from typing import Self
from uuid import UUID

from modules.tasks.domain.entities import Task
from modules.tasks.domain.enums import TaskStatus


@dataclass(frozen=True, slots=True, kw_only=True)
class TaskDTO:
    id: UUID
    project_id: UUID
    title: str
    description: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, task: Task) -> Self:
        return cls(
            id=task.id_.value,
            project_id=task.props.project_id,
            title=task.props.title.value,
            description=task.props.description.value,
            status=task.props.status,
            created_at=task.created_at_,
            updated_at=task.updated_at_,
        )
```

`src/modules/tasks/application/commands/create_task.py` :

```python
"""Create a task."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.application.unit_of_work import UnitOfWork
from modules.tasks.application.dto import TaskDTO
from modules.tasks.domain.entities import Task
from modules.tasks.domain.errors import (
    TaskProjectArchivedError,
    TaskProjectNotFoundError,
)
from modules.tasks.domain.ports import ProjectLookupPort, TaskRepositoryPort

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class CreateTaskRequest:
    project_id: UUID
    title: str
    description: str = ""


class CreateTaskCommand:
    """Create a task in an active project."""

    def __init__(
        self,
        repository: TaskRepositoryPort,
        project_lookup: ProjectLookupPort,
        uow: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._project_lookup = project_lookup
        self._uow = uow

    async def execute(self, request: CreateTaskRequest) -> TaskDTO:
        task = Task.create(
            project_id=request.project_id,
            title=request.title,
            description=request.description,
        )
        project = await self._project_lookup.get(request.project_id)
        if project is None:
            raise TaskProjectNotFoundError(request.project_id)
        if not project.is_active:
            raise TaskProjectArchivedError(request.project_id)
        await self._repository.add(task)
        await self._uow.commit()
        log.info("Task created: %s", task.id_.value)
        return TaskDTO.from_entity(task)
```

`src/modules/tasks/application/commands/update_task.py` :

```python
"""Update the title and/or description of a task."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.application.unit_of_work import UnitOfWork
from modules.tasks.application.dto import TaskDTO
from modules.tasks.domain.errors import TaskNotFoundError
from modules.tasks.domain.ports import TaskRepositoryPort
from modules.tasks.domain.value_objects import TaskId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class UpdateTaskRequest:
    task_id: UUID
    title: str | None = None
    description: str | None = None


class UpdateTaskCommand:
    """Change the title and/or description of an open task."""

    def __init__(self, repository: TaskRepositoryPort, uow: UnitOfWork) -> None:
        self._repository = repository
        self._uow = uow

    async def execute(self, request: UpdateTaskRequest) -> TaskDTO:
        task = await self._repository.get_by_id(TaskId(request.task_id))
        if task is None:
            raise TaskNotFoundError(request.task_id)
        if request.title is not None:
            task.rename(request.title)
        if request.description is not None:
            task.change_description(request.description)
        await self._repository.save(task)
        await self._uow.commit()
        log.info("Task updated: %s", request.task_id)
        return TaskDTO.from_entity(task)
```

`src/modules/tasks/application/commands/change_task_status.py` :

```python
"""Move a task through its lifecycle."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.application.unit_of_work import UnitOfWork
from modules.tasks.application.dto import TaskDTO
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.errors import TaskNotFoundError
from modules.tasks.domain.ports import TaskRepositoryPort
from modules.tasks.domain.value_objects import TaskId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class ChangeTaskStatusRequest:
    task_id: UUID
    status: TaskStatus


class ChangeTaskStatusCommand:
    """Change the status of a task (todo → in_progress → done, or cancelled)."""

    def __init__(self, repository: TaskRepositoryPort, uow: UnitOfWork) -> None:
        self._repository = repository
        self._uow = uow

    async def execute(self, request: ChangeTaskStatusRequest) -> TaskDTO:
        task = await self._repository.get_by_id(TaskId(request.task_id))
        if task is None:
            raise TaskNotFoundError(request.task_id)
        task.change_status(request.status)
        await self._repository.save(task)
        await self._uow.commit()
        log.info("Task %s moved to %s", request.task_id, request.status)
        return TaskDTO.from_entity(task)
```

`src/modules/tasks/application/commands/delete_task.py` :

```python
"""Delete a task."""

import logging
from dataclasses import dataclass
from uuid import UUID

from core.application.unit_of_work import UnitOfWork
from modules.tasks.domain.errors import TaskNotFoundError
from modules.tasks.domain.ports import TaskRepositoryPort
from modules.tasks.domain.value_objects import TaskId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeleteTaskRequest:
    task_id: UUID


class DeleteTaskCommand:
    """Delete a task."""

    def __init__(self, repository: TaskRepositoryPort, uow: UnitOfWork) -> None:
        self._repository = repository
        self._uow = uow

    async def execute(self, request: DeleteTaskRequest) -> None:
        task = await self._repository.get_by_id(TaskId(request.task_id))
        if task is None:
            raise TaskNotFoundError(request.task_id)
        await self._repository.delete(task)
        await self._uow.commit()
        log.info("Task deleted: %s", request.task_id)
```

`src/modules/tasks/application/commands/__init__.py` :

```python
from .change_task_status import ChangeTaskStatusCommand, ChangeTaskStatusRequest
from .create_task import CreateTaskCommand, CreateTaskRequest
from .delete_task import DeleteTaskCommand, DeleteTaskRequest
from .update_task import UpdateTaskCommand, UpdateTaskRequest

__all__ = [
    "ChangeTaskStatusCommand",
    "ChangeTaskStatusRequest",
    "CreateTaskCommand",
    "CreateTaskRequest",
    "DeleteTaskCommand",
    "DeleteTaskRequest",
    "UpdateTaskCommand",
    "UpdateTaskRequest",
]
```

`src/modules/tasks/application/queries/get_task_by_id.py` :

```python
"""Get one task."""

from dataclasses import dataclass
from uuid import UUID

from modules.tasks.application.dto import TaskDTO
from modules.tasks.domain.errors import TaskNotFoundError
from modules.tasks.domain.ports import TaskRepositoryPort
from modules.tasks.domain.value_objects import TaskId


@dataclass(frozen=True, slots=True, kw_only=True)
class GetTaskByIdRequest:
    task_id: UUID


class GetTaskByIdQuery:
    """Return one task."""

    def __init__(self, repository: TaskRepositoryPort) -> None:
        self._repository = repository

    async def execute(self, request: GetTaskByIdRequest) -> TaskDTO:
        task = await self._repository.get_by_id(TaskId(request.task_id))
        if task is None:
            raise TaskNotFoundError(request.task_id)
        return TaskDTO.from_entity(task)
```

`src/modules/tasks/application/queries/list_tasks.py` :

```python
"""List tasks."""

from dataclasses import dataclass
from uuid import UUID

from core.domain.pagination import Page, PageParams, Sort
from modules.tasks.application.dto import TaskDTO
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.ports import TaskRepositoryPort


@dataclass(frozen=True, slots=True, kw_only=True)
class ListTasksRequest:
    page: int = 1
    size: int = 20
    project_id: UUID | None = None
    status: TaskStatus | None = None
    sort: str = "-created_at"


class ListTasksQuery:
    """Return a page of tasks, optionally filtered by project and status."""

    def __init__(self, repository: TaskRepositoryPort) -> None:
        self._repository = repository

    async def execute(self, request: ListTasksRequest) -> Page[TaskDTO]:
        filters: dict[str, object] = {}
        if request.project_id is not None:
            filters["project_id"] = request.project_id
        if request.status is not None:
            filters["status"] = request.status.value
        page = await self._repository.list_page(
            PageParams(page=request.page, size=request.size),
            sort=Sort.parse(request.sort),
            filters=filters,
        )
        return page.map(TaskDTO.from_entity)
```

`src/modules/tasks/application/queries/__init__.py` :

```python
from .get_task_by_id import GetTaskByIdQuery, GetTaskByIdRequest
from .list_tasks import ListTasksQuery, ListTasksRequest

__all__ = [
    "GetTaskByIdQuery",
    "GetTaskByIdRequest",
    "ListTasksQuery",
    "ListTasksRequest",
]
```

`src/modules/tasks/application/event_handlers/cancel_tasks_on_project_archived.py` :

```python
"""Cancel the open tasks of an archived project."""

import logging

from core.application.event_bus import EventHandler
from modules.projects.public import ProjectArchived
from modules.tasks.domain.ports import TaskRepositoryPort

log = logging.getLogger(__name__)


class CancelTasksOnProjectArchived(EventHandler[ProjectArchived]):
    """Runs in the transaction that archives the project; never commits."""

    def __init__(self, repository: TaskRepositoryPort) -> None:
        self._repository = repository

    async def handle(self, event: ProjectArchived) -> None:
        tasks = await self._repository.list_open_by_project(event.project_id)
        for task in tasks:
            task.cancel()
            await self._repository.save(task)
        log.info(
            "Cancelled %d task(s) of archived project %s", len(tasks), event.project_id
        )
```

`src/modules/tasks/application/event_handlers/delete_tasks_on_project_deleted.py` :

```python
"""Delete the tasks of a deleted project."""

import logging

from core.application.event_bus import EventHandler
from modules.projects.public import ProjectDeleted
from modules.tasks.domain.ports import TaskRepositoryPort

log = logging.getLogger(__name__)


class DeleteTasksOnProjectDeleted(EventHandler[ProjectDeleted]):
    """Runs in the transaction that deletes the project; never commits."""

    def __init__(self, repository: TaskRepositoryPort) -> None:
        self._repository = repository

    async def handle(self, event: ProjectDeleted) -> None:
        await self._repository.delete_by_project(event.project_id)
        log.info("Deleted the tasks of project %s", event.project_id)
```

`src/modules/tasks/application/event_handlers/__init__.py` :

```python
from .cancel_tasks_on_project_archived import CancelTasksOnProjectArchived
from .delete_tasks_on_project_deleted import DeleteTasksOnProjectDeleted

__all__ = ["CancelTasksOnProjectArchived", "DeleteTasksOnProjectDeleted"]
```

- [ ] **Step 4: Vérifier le succès**

Run: `uv run pytest tests/unit -v`
Expected: tout passe.

- [ ] **Step 5: Lint et commit**

```bash
make format && make lint
git add src/modules/tasks tests/fakes tests/unit/tasks
git commit -m "feat(tasks): add task use cases and project event handlers" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 16: `tasks` — persistance, adaptateur vers `projects` et câblage des événements

**Files:**
- Create: `src/modules/tasks/infrastructure/__init__.py` (vide), `src/modules/tasks/infrastructure/models/{__init__,task_model}.py`, `src/modules/tasks/infrastructure/mappers/{__init__,task_mapper}.py`, `src/modules/tasks/infrastructure/repositories/{__init__,task_repository}.py`, `src/modules/tasks/infrastructure/adapters/{__init__,projects_lookup}.py`, `src/modules/tasks/provider.py`
- Modify: `migrations/versions/2026_09_17_1200-0001_initial_schema.py`, `src/app/models.py`, `src/app/providers.py`, `src/app/event_handlers.py`
- Test: `tests/integration/tasks/__init__.py` (vide), `tests/integration/tasks/test_task_repository.py`, `tests/integration/tasks/test_project_events.py`

**Interfaces:**
- Consumes: Tasks 7, 9, 12 (même schéma que `projects`) ; `ProjectsPublicApi` (Task 11) ; application `tasks` (Task 15).
- Produces:
  - Table `tasks` : `id` uuid PK (`pk_tasks`), `project_id` uuid (sans clé étrangère), `title` varchar(200), `description` text, `status` varchar(20) + CHECK (`ck_tasks_status`), `created_at`, `updated_at` ; index `ix_tasks_project_id_status (project_id, status)` ; tous NOT NULL.
  - `TaskModel`, `TaskMapper`, `SqlaTaskRepository(session, tracker)` (tri : `title`, `status`, `created_at`, `updated_at` ; filtres : `project_id`, `status`).
  - `modules.tasks.infrastructure.adapters.ProjectsModuleLookup(projects: ProjectsPublicApi)` implémente `ProjectLookupPort`.
  - `modules.tasks.provider.TasksProvider` (REQUEST) : `TaskRepositoryPort`, `ProjectLookupPort`, les 6 use cases, les 2 handlers.
  - `app.event_handlers.EventHandlersProvider` : `ProjectArchived → (CancelTasksOnProjectArchived,)`, `ProjectDeleted → (DeleteTasksOnProjectDeleted,)`.

- [ ] **Step 1: Écrire les tests d'intégration qui échouent**

`tests/integration/tasks/test_task_repository.py` :

```python
"""SqlaTaskRepository against PostgreSQL."""

from collections.abc import Sequence
from uuid import uuid4

from dishka import AsyncContainer

from core.application.unit_of_work import UnitOfWork
from core.domain.pagination import PageParams
from modules.tasks.domain.entities import Task
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.ports import TaskRepositoryPort


async def persist(container: AsyncContainer, tasks: Sequence[Task]) -> None:
    async with container() as scope:
        repository = await scope.get(TaskRepositoryPort)
        for task in tasks:
            await repository.add(task)
        await (await scope.get(UnitOfWork)).commit()


async def test_add_then_get_by_id_round_trips_every_field(
    container: AsyncContainer,
) -> None:
    task = Task.create(project_id=uuid4(), title="Draft", description="Text")
    task.start()
    await persist(container, [task])

    async with container() as scope:
        loaded = await (await scope.get(TaskRepositoryPort)).get_by_id(task.id_)

    assert loaded is not None
    assert loaded.props == task.props
    assert loaded.created_at_ == task.created_at_


async def test_list_open_by_project_returns_open_tasks_of_that_project(
    container: AsyncContainer,
) -> None:
    project_id = uuid4()
    todo = Task.create(project_id=project_id, title="Todo")
    started = Task.create(project_id=project_id, title="Started")
    started.start()
    done = Task.create(project_id=project_id, title="Done")
    done.complete()
    elsewhere = Task.create(project_id=uuid4(), title="Elsewhere")
    await persist(container, [todo, started, done, elsewhere])

    async with container() as scope:
        repository = await scope.get(TaskRepositoryPort)
        tasks = await repository.list_open_by_project(project_id)

    assert {task.id_ for task in tasks} == {todo.id_, started.id_}


async def test_delete_by_project_keeps_other_projects_tasks(
    container: AsyncContainer,
) -> None:
    project_id, other_project_id = uuid4(), uuid4()
    await persist(
        container,
        [
            Task.create(project_id=project_id, title="A"),
            Task.create(project_id=project_id, title="B"),
            Task.create(project_id=other_project_id, title="C"),
        ],
    )

    async with container() as scope:
        await (await scope.get(TaskRepositoryPort)).delete_by_project(project_id)
        await (await scope.get(UnitOfWork)).commit()

    async with container() as scope:
        repository = await scope.get(TaskRepositoryPort)
        removed = await repository.list_page(
            PageParams(), filters={"project_id": project_id}
        )
        kept = await repository.list_page(
            PageParams(), filters={"project_id": other_project_id}
        )
    assert (removed.total, kept.total) == (0, 1)


async def test_list_page_filters_by_project_and_status(
    container: AsyncContainer,
) -> None:
    project_id = uuid4()
    first = Task.create(project_id=project_id, title="First")
    first.complete()
    second = Task.create(project_id=project_id, title="Second")
    await persist(container, [first, second, Task.create(project_id=uuid4(), title="X")])

    async with container() as scope:
        page = await (await scope.get(TaskRepositoryPort)).list_page(
            PageParams(),
            filters={"project_id": project_id, "status": TaskStatus.TODO.value},
        )

    assert [task.props.title.value for task in page.items] == ["Second"]
```

`tests/integration/tasks/test_project_events.py` :

```python
"""Cross-module reactions to project events, inside one transaction."""

from typing import override
from uuid import UUID

import pytest
from dishka import AsyncContainer, Provider, Scope, provide

from app.main import create_app
from core.application.event_bus import EventHandler, EventHandlerRegistry
from core.infrastructure.settings import Settings
from modules.projects.application.commands import (
    ArchiveProjectCommand,
    ArchiveProjectRequest,
    CreateProjectCommand,
    CreateProjectRequest,
    DeleteProjectCommand,
    DeleteProjectRequest,
)
from modules.projects.application.dto import ProjectDTO
from modules.projects.application.queries import (
    GetProjectByIdQuery,
    GetProjectByIdRequest,
)
from modules.projects.domain.enums import ProjectStatus
from modules.projects.public import ProjectArchived
from modules.tasks.application.commands import (
    ChangeTaskStatusCommand,
    ChangeTaskStatusRequest,
    CreateTaskCommand,
    CreateTaskRequest,
)
from modules.tasks.application.dto import TaskDTO
from modules.tasks.application.event_handlers import CancelTasksOnProjectArchived
from modules.tasks.application.queries import GetTaskByIdQuery, GetTaskByIdRequest
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.errors import TaskNotFoundError


async def create_project(container: AsyncContainer, name: str) -> ProjectDTO:
    async with container() as scope:
        command = await scope.get(CreateProjectCommand)
        return await command.execute(CreateProjectRequest(name=name))


async def create_task(
    container: AsyncContainer, project_id: UUID, title: str
) -> TaskDTO:
    async with container() as scope:
        command = await scope.get(CreateTaskCommand)
        return await command.execute(
            CreateTaskRequest(project_id=project_id, title=title)
        )


async def get_task(container: AsyncContainer, task_id: UUID) -> TaskDTO:
    async with container() as scope:
        query = await scope.get(GetTaskByIdQuery)
        return await query.execute(GetTaskByIdRequest(task_id=task_id))


async def test_archiving_a_project_cancels_its_open_tasks(
    container: AsyncContainer,
) -> None:
    project = await create_project(container, "Website")
    todo = await create_task(container, project.id, "Todo")
    done = await create_task(container, project.id, "Done")
    async with container() as scope:
        await (await scope.get(ChangeTaskStatusCommand)).execute(
            ChangeTaskStatusRequest(task_id=done.id, status=TaskStatus.DONE)
        )

    async with container() as scope:
        await (await scope.get(ArchiveProjectCommand)).execute(
            ArchiveProjectRequest(project_id=project.id)
        )

    assert (await get_task(container, todo.id)).status is TaskStatus.CANCELLED
    assert (await get_task(container, done.id)).status is TaskStatus.DONE


async def test_deleting_a_project_deletes_its_tasks(container: AsyncContainer) -> None:
    project = await create_project(container, "Website")
    other_project = await create_project(container, "Intranet")
    task = await create_task(container, project.id, "Todo")
    other_task = await create_task(container, other_project.id, "Todo")

    async with container() as scope:
        await (await scope.get(DeleteProjectCommand)).execute(
            DeleteProjectRequest(project_id=project.id)
        )

    with pytest.raises(TaskNotFoundError):
        await get_task(container, task.id)
    assert (await get_task(container, other_task.id)).id == other_task.id


class ExplodingHandler(EventHandler[ProjectArchived]):
    @override
    async def handle(self, event: ProjectArchived) -> None:
        raise RuntimeError("boom")


class ExplodingHandlersProvider(Provider):
    scope = Scope.REQUEST

    handler = provide(ExplodingHandler)

    @provide(scope=Scope.APP)
    def registry(self) -> EventHandlerRegistry:
        return EventHandlerRegistry(
            handlers={ProjectArchived: (CancelTasksOnProjectArchived, ExplodingHandler)}
        )


async def test_a_failing_handler_rolls_back_the_whole_transaction(
    settings: Settings,
) -> None:
    app = create_app(settings, ExplodingHandlersProvider())
    container: AsyncContainer = app.state.dishka_container
    try:
        project = await create_project(container, "Website")
        task = await create_task(container, project.id, "Todo")

        async with container() as scope:
            command = await scope.get(ArchiveProjectCommand)
            with pytest.raises(RuntimeError, match="boom"):
                await command.execute(ArchiveProjectRequest(project_id=project.id))

        async with container() as scope:
            query = await scope.get(GetProjectByIdQuery)
            reloaded = await query.execute(GetProjectByIdRequest(project_id=project.id))
        assert reloaded.status is ProjectStatus.ACTIVE
        assert (await get_task(container, task.id)).status is TaskStatus.TODO
    finally:
        await container.close()
```

`@override` indique à ruff (ARG002) que l'argument inutilisé de `ExplodingHandler.handle` est imposé par le protocole.

- [ ] **Step 2: Vérifier l'échec**

Run: `uv run pytest tests/integration/tasks -v`
Expected: FAIL (`TaskRepositoryPort` / `CreateTaskCommand` non fournis par Dishka).

- [ ] **Step 3: Implémenter la persistance et l'adaptateur**

`src/modules/tasks/infrastructure/models/task_model.py` :

```python
"""ORM model of the `tasks` table."""

from uuid import UUID

from sqlalchemy import CheckConstraint, Index, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from core.infrastructure.db.base import Base
from core.infrastructure.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from modules.tasks.domain.enums import TaskStatus

STATUS_VALUES = ", ".join(f"'{status.value}'" for status in TaskStatus)


class TaskModel(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """`project_id` has no foreign key: `projects` belongs to another module."""

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(f"status IN ({STATUS_VALUES})", name="status"),
        Index("ix_tasks_project_id_status", "project_id", "status"),
    )

    project_id: Mapped[UUID] = mapped_column(Uuid)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))
```

`src/modules/tasks/infrastructure/models/__init__.py` :

```python
from .task_model import TaskModel

__all__ = ["TaskModel"]
```

`src/modules/tasks/infrastructure/mappers/task_mapper.py` :

```python
"""Mapping between `Task` and `TaskModel`."""

from core.infrastructure.db.mapper import EntityMapper
from modules.tasks.domain.entities import Task, TaskProps
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.value_objects import TaskDescription, TaskId, TaskTitle
from modules.tasks.infrastructure.models import TaskModel


class TaskMapper(EntityMapper[Task, TaskModel]):
    def to_model(self, entity: Task) -> TaskModel:
        return TaskModel(
            id=entity.id_.value,
            project_id=entity.props.project_id,
            title=entity.props.title.value,
            description=entity.props.description.value,
            status=entity.props.status.value,
            created_at=entity.created_at_,
            updated_at=entity.updated_at_,
        )

    def to_entity(self, model: TaskModel) -> Task:
        return Task(
            id_=TaskId(model.id),
            props=TaskProps(
                project_id=model.project_id,
                title=TaskTitle(model.title),
                description=TaskDescription(model.description),
                status=TaskStatus(model.status),
            ),
            created_at_=model.created_at,
            updated_at_=model.updated_at,
        )
```

`src/modules/tasks/infrastructure/mappers/__init__.py` :

```python
from .task_mapper import TaskMapper

__all__ = ["TaskMapper"]
```

`src/modules/tasks/infrastructure/repositories/task_repository.py` :

```python
"""SQLAlchemy repository of tasks."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.infrastructure.db.repository import SqlaRepository
from core.infrastructure.db.tracker import AggregateTracker
from modules.tasks.domain.entities import Task
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.ports import TaskRepositoryPort
from modules.tasks.infrastructure.mappers import TaskMapper
from modules.tasks.infrastructure.models import TaskModel

OPEN_STATUSES = [status.value for status in TaskStatus if not status.is_terminal]


class SqlaTaskRepository(SqlaRepository[Task, TaskModel], TaskRepositoryPort):
    sortable_fields = frozenset({"title", "status", "created_at", "updated_at"})
    filterable_fields = frozenset({"project_id", "status"})

    def __init__(self, session: AsyncSession, tracker: AggregateTracker) -> None:
        super().__init__(
            session=session, tracker=tracker, model=TaskModel, mapper=TaskMapper()
        )

    async def list_open_by_project(self, project_id: UUID) -> list[Task]:
        statement = (
            select(TaskModel)
            .where(
                TaskModel.project_id == project_id,
                TaskModel.status.in_(OPEN_STATUSES),
            )
            .order_by(TaskModel.created_at, TaskModel.id)
        )
        models = (await self._session.scalars(statement)).all()
        tasks = [self._mapper.to_entity(model) for model in models]
        for task in tasks:
            self._tracker.track(task)
        return tasks

    async def delete_by_project(self, project_id: UUID) -> None:
        statement = delete(TaskModel).where(TaskModel.project_id == project_id)
        await self._session.execute(statement)
```

`src/modules/tasks/infrastructure/repositories/__init__.py` :

```python
from .task_repository import SqlaTaskRepository

__all__ = ["SqlaTaskRepository"]
```

`src/modules/tasks/infrastructure/adapters/projects_lookup.py` :

```python
"""`ProjectLookupPort` backed by the public API of the projects module."""

from uuid import UUID

from modules.projects.public import ProjectsPublicApi
from modules.tasks.domain.ports import ProjectLookupPort, ProjectRef


class ProjectsModuleLookup(ProjectLookupPort):
    """Anti-corruption layer: translates `ProjectSummary` into `ProjectRef`."""

    def __init__(self, projects: ProjectsPublicApi) -> None:
        self._projects = projects

    async def get(self, project_id: UUID) -> ProjectRef | None:
        summary = await self._projects.get_summary(project_id)
        if summary is None:
            return None
        return ProjectRef(id=summary.id, is_active=summary.is_active)
```

`src/modules/tasks/infrastructure/adapters/__init__.py` :

```python
from .projects_lookup import ProjectsModuleLookup

__all__ = ["ProjectsModuleLookup"]
```

`src/modules/tasks/provider.py` :

```python
"""Dishka provider of the tasks module."""

from dishka import Provider, Scope, provide, provide_all

from modules.tasks.application.commands import (
    ChangeTaskStatusCommand,
    CreateTaskCommand,
    DeleteTaskCommand,
    UpdateTaskCommand,
)
from modules.tasks.application.event_handlers import (
    CancelTasksOnProjectArchived,
    DeleteTasksOnProjectDeleted,
)
from modules.tasks.application.queries import GetTaskByIdQuery, ListTasksQuery
from modules.tasks.domain.ports import ProjectLookupPort, TaskRepositoryPort
from modules.tasks.infrastructure.adapters import ProjectsModuleLookup
from modules.tasks.infrastructure.repositories import SqlaTaskRepository


class TasksProvider(Provider):
    scope = Scope.REQUEST

    repository = provide(SqlaTaskRepository, provides=TaskRepositoryPort)
    project_lookup = provide(ProjectsModuleLookup, provides=ProjectLookupPort)
    use_cases = provide_all(
        CreateTaskCommand,
        UpdateTaskCommand,
        ChangeTaskStatusCommand,
        DeleteTaskCommand,
        GetTaskByIdQuery,
        ListTasksQuery,
    )
    event_handlers = provide_all(
        CancelTasksOnProjectArchived, DeleteTasksOnProjectDeleted
    )
```

- [ ] **Step 4: Câbler le module dans `app` et compléter la migration**

`src/app/models.py` (remplacer) :

```python
"""Import every ORM model so that `Base.metadata` describes the whole schema."""

from core.infrastructure.db.base import Base
from modules.projects.infrastructure.models import ProjectModel
from modules.tasks.infrastructure.models import TaskModel

__all__ = ["Base", "ProjectModel", "TaskModel"]
```

`src/app/providers.py` (remplacer) :

```python
"""Every Dishka provider of the application."""

from dishka import Provider

from app.event_handlers import EventHandlersProvider
from core.infrastructure.provider import core_providers
from modules.projects.provider import ProjectsProvider
from modules.tasks.provider import TasksProvider


def get_providers() -> tuple[Provider, ...]:
    return (
        *core_providers(),
        EventHandlersProvider(),
        ProjectsProvider(),
        TasksProvider(),
    )
```

`src/app/event_handlers.py` (remplacer) :

```python
"""Wiring of domain events to the handlers that react to them."""

from dishka import Provider, Scope, provide

from core.application.event_bus import EventHandlerRegistry
from modules.projects.public import ProjectArchived, ProjectDeleted
from modules.tasks.application.event_handlers import (
    CancelTasksOnProjectArchived,
    DeleteTasksOnProjectDeleted,
)


class EventHandlersProvider(Provider):
    """Register here every handler that must run when a domain event is published."""

    @provide(scope=Scope.APP)
    def registry(self) -> EventHandlerRegistry:
        return EventHandlerRegistry(
            handlers={
                ProjectArchived: (CancelTasksOnProjectArchived,),
                ProjectDeleted: (DeleteTasksOnProjectDeleted,),
            }
        )
```

Dans `migrations/versions/2026_09_17_1200-0001_initial_schema.py`, remplacer `upgrade` et `downgrade` par :

```python
def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('active', 'archived')", name=op.f("ck_projects_status")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_projects")),
        sa.UniqueConstraint("name", name=op.f("uq_projects_name")),
    )
    op.create_index(op.f("ix_projects_status"), "projects", ["status"], unique=False)
    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('todo', 'in_progress', 'done', 'cancelled')",
            name=op.f("ck_tasks_status"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tasks")),
    )
    op.create_index(
        "ix_tasks_project_id_status", "tasks", ["project_id", "status"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_tasks_project_id_status", table_name="tasks")
    op.drop_table("tasks")
    op.drop_index(op.f("ix_projects_status"), table_name="projects")
    op.drop_table("projects")
```

La migration `0001` n'ayant jamais été publiée, on la modifie au lieu d'en créer une seconde. Si une base locale a déjà été migrée pendant le développement : `docker compose down -v`.

- [ ] **Step 5: Vérifier le succès**

Run: `uv run pytest -v`
Expected: tous les tests passent, y compris `test_migrations_match_the_orm_models` et `test_a_failing_handler_rolls_back_the_whole_transaction`.

- [ ] **Step 6: Lint et commit**

```bash
make format && make lint
git add migrations src/modules/tasks src/app tests/integration/tasks
git commit -m "feat(tasks): persist tasks and react to project events in the same transaction" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 17: `tasks` — API HTTP et flux inter-modules

**Files:**
- Create: `src/modules/tasks/presentation/__init__.py` (vide), `src/modules/tasks/presentation/http/__init__.py` (vide), `src/modules/tasks/presentation/http/schemas.py`, `src/modules/tasks/presentation/http/router.py`, `src/modules/tasks/presentation/http/controllers/{__init__,create_task,list_tasks,get_task,update_task,change_task_status,delete_task}.py`
- Modify: `src/app/routers.py`
- Test: `tests/integration/tasks/test_tasks_api.py`

**Interfaces:**
- Consumes: application `tasks` (Task 15), `TasksProvider` (Task 16), helpers HTTP (Task 8), fixture `client` (Task 9).
- Produces:
  - `modules.tasks.presentation.http.schemas` : `SORT_DESCRIPTION`, `CreateTaskBody(project_id, title, description="")`, `UpdateTaskBody(title=None, description=None)`, `ChangeTaskStatusBody(status)` (tous `extra="forbid"`), `TaskResponse(id, project_id, title, description, status, created_at, updated_at)`.
  - `modules.tasks.presentation.http.router.create_tasks_router() -> APIRouter` (tag `Tasks`) : `POST /tasks`, `GET /tasks`, `GET /tasks/{task_id}`, `PATCH /tasks/{task_id}`, `PATCH /tasks/{task_id}/status`, `DELETE /tasks/{task_id}`, monté sous `/api/v1`.

- [ ] **Step 1: Écrire les tests d'intégration qui échouent**

`tests/integration/tasks/test_tasks_api.py` :

```python
"""Tasks HTTP API and its interactions with projects, against PostgreSQL."""

from http import HTTPStatus
from typing import Any, cast
from uuid import uuid4

from httpx import AsyncClient, Response

PROJECTS_URL = "/api/v1/projects"
TASKS_URL = "/api/v1/tasks"


async def create_project(client: AsyncClient, name: str = "Website") -> str:
    response = await client.post(PROJECTS_URL, json={"name": name})
    assert response.status_code == HTTPStatus.CREATED, response.text
    return cast(str, response.json()["id"])


async def create_task(
    client: AsyncClient, project_id: str, title: str = "Write copy"
) -> dict[str, Any]:
    response = await client.post(
        TASKS_URL, json={"project_id": project_id, "title": title}
    )
    assert response.status_code == HTTPStatus.CREATED, response.text
    return cast(dict[str, Any], response.json())


async def change_status(client: AsyncClient, task_id: str, status: str) -> Response:
    return await client.patch(f"{TASKS_URL}/{task_id}/status", json={"status": status})


async def test_create_then_get_a_task(client: AsyncClient) -> None:
    project_id = await create_project(client)
    created = await create_task(client, project_id, title=" Draft ")

    response = await client.get(f"{TASKS_URL}/{created['id']}")

    assert (created["project_id"], created["title"], created["status"]) == (
        project_id,
        "Draft",
        "todo",
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == created


async def test_task_for_an_unknown_project_is_not_found(client: AsyncClient) -> None:
    response = await client.post(
        TASKS_URL, json={"project_id": str(uuid4()), "title": "Draft"}
    )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["code"] == "task_project_not_found"


async def test_task_for_an_archived_project_is_a_conflict(client: AsyncClient) -> None:
    project_id = await create_project(client)
    await client.post(f"{PROJECTS_URL}/{project_id}/archive")

    response = await client.post(
        TASKS_URL, json={"project_id": project_id, "title": "Draft"}
    )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()["code"] == "task_project_archived"


async def test_update_a_task(client: AsyncClient) -> None:
    task = await create_task(client, await create_project(client))
    url = f"{TASKS_URL}/{task['id']}"

    updated = await client.patch(url, json={"title": "New", "description": "Text"})
    await change_status(client, task["id"], "done")
    closed = await client.patch(url, json={"title": "Too late"})

    assert updated.status_code == HTTPStatus.OK
    assert (updated.json()["title"], updated.json()["description"]) == ("New", "Text")
    assert closed.status_code == HTTPStatus.CONFLICT
    assert closed.json()["code"] == "task_closed"


async def test_status_transitions(client: AsyncClient) -> None:
    task = await create_task(client, await create_project(client))

    started = await change_status(client, task["id"], "in_progress")
    back_to_todo = await change_status(client, task["id"], "todo")
    done = await change_status(client, task["id"], "done")

    assert started.status_code == HTTPStatus.OK
    assert started.json()["status"] == "in_progress"
    assert back_to_todo.status_code == HTTPStatus.CONFLICT
    assert back_to_todo.json()["code"] == "invalid_task_transition"
    assert back_to_todo.json()["details"] == {
        "task_id": task["id"],
        "current": "in_progress",
        "target": "todo",
    }
    assert done.json()["status"] == "done"


async def test_unknown_status_is_a_request_validation_error(
    client: AsyncClient,
) -> None:
    task = await create_task(client, await create_project(client))

    response = await change_status(client, task["id"], "paused")

    assert response.status_code == HTTPStatus.UNPROCESSABLE_CONTENT
    assert response.json()["code"] == "request_validation_error"


async def test_delete_a_task(client: AsyncClient) -> None:
    task = await create_task(client, await create_project(client))
    url = f"{TASKS_URL}/{task['id']}"

    deleted = await client.delete(url)
    fetched = await client.get(url)

    assert deleted.status_code == HTTPStatus.NO_CONTENT
    assert fetched.status_code == HTTPStatus.NOT_FOUND
    assert fetched.json()["code"] == "task_not_found"


async def test_list_tasks_filters_by_project_and_status(client: AsyncClient) -> None:
    website = await create_project(client, "Website")
    intranet = await create_project(client, "Intranet")
    first = await create_task(client, website, "First")
    await create_task(client, website, "Second")
    await create_task(client, intranet, "Other")
    await change_status(client, first["id"], "done")

    response = await client.get(
        TASKS_URL, params={"project_id": website, "status": "todo", "sort": "title"}
    )

    body = response.json()
    assert response.status_code == HTTPStatus.OK
    assert [item["title"] for item in body["items"]] == ["Second"]
    assert body["total"] == 1


async def test_archiving_a_project_cancels_its_open_tasks(client: AsyncClient) -> None:
    project_id = await create_project(client)
    todo = await create_task(client, project_id, "Todo")
    done = await create_task(client, project_id, "Done")
    await change_status(client, done["id"], "done")

    archived = await client.post(f"{PROJECTS_URL}/{project_id}/archive")
    todo_after = await client.get(f"{TASKS_URL}/{todo['id']}")
    done_after = await client.get(f"{TASKS_URL}/{done['id']}")

    assert archived.status_code == HTTPStatus.OK
    assert todo_after.json()["status"] == "cancelled"
    assert done_after.json()["status"] == "done"


async def test_deleting_a_project_deletes_only_its_tasks(client: AsyncClient) -> None:
    website = await create_project(client, "Website")
    intranet = await create_project(client, "Intranet")
    await create_task(client, website, "Website task")
    kept = await create_task(client, intranet, "Intranet task")

    deleted = await client.delete(f"{PROJECTS_URL}/{website}")
    remaining = await client.get(TASKS_URL)

    assert deleted.status_code == HTTPStatus.NO_CONTENT
    assert [item["id"] for item in remaining.json()["items"]] == [kept["id"]]
```

- [ ] **Step 2: Vérifier l'échec**

Run: `uv run pytest tests/integration/tasks/test_tasks_api.py -v`
Expected: FAIL (404 sur `/api/v1/tasks`).

- [ ] **Step 3: Implémenter les schémas et contrôleurs**

`src/modules/tasks/presentation/http/schemas.py` :

```python
"""HTTP models of the tasks module."""

from datetime import datetime
from typing import Final
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from modules.tasks.domain.enums import TaskStatus
from modules.tasks.domain.value_objects.task_description import (
    MAX_LENGTH as DESCRIPTION_MAX_LENGTH,
)
from modules.tasks.domain.value_objects.task_title import (
    MAX_LENGTH as TITLE_MAX_LENGTH,
)

SORT_DESCRIPTION: Final[str] = (
    "Field to sort by, prefixed with '-' for descending order. "
    "Allowed: title, status, created_at, updated_at."
)


class CreateTaskBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: UUID
    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    description: str = Field(default="", max_length=DESCRIPTION_MAX_LENGTH)


class UpdateTaskBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=TITLE_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)


class ChangeTaskStatusBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: TaskStatus


class TaskResponse(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
```

`src/modules/tasks/presentation/http/controllers/create_task.py` :

```python
"""POST /tasks."""

from http import HTTPStatus

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.tasks.application.commands import CreateTaskCommand, CreateTaskRequest
from modules.tasks.presentation.http.schemas import CreateTaskBody, TaskResponse


def create_create_task_router() -> APIRouter:
    router = APIRouter()

    @router.post(
        "/tasks",
        status_code=HTTPStatus.CREATED,
        response_model=TaskResponse,
        responses=error_responses(
            HTTPStatus.NOT_FOUND, HTTPStatus.CONFLICT, HTTPStatus.UNPROCESSABLE_CONTENT
        ),
        summary="Create a task in an active project",
    )
    @inject
    async def create_task(
        body: CreateTaskBody, command: FromDishka[CreateTaskCommand]
    ) -> TaskResponse:
        task = await command.execute(
            CreateTaskRequest(
                project_id=body.project_id,
                title=body.title,
                description=body.description,
            )
        )
        return TaskResponse.model_validate(task, from_attributes=True)

    return router
```

`src/modules/tasks/presentation/http/controllers/list_tasks.py` :

```python
"""GET /tasks."""

from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Query

from core.domain.pagination import MAX_PAGE_SIZE
from core.presentation.http.errors import error_responses
from core.presentation.http.pagination import PageResponse, to_page_response
from modules.tasks.application.queries import ListTasksQuery, ListTasksRequest
from modules.tasks.domain.enums import TaskStatus
from modules.tasks.presentation.http.schemas import SORT_DESCRIPTION, TaskResponse


def create_list_tasks_router() -> APIRouter:
    router = APIRouter()

    @router.get(
        "/tasks",
        response_model=PageResponse[TaskResponse],
        responses=error_responses(HTTPStatus.UNPROCESSABLE_CONTENT),
        summary="List tasks",
    )
    @inject
    async def list_tasks(
        query: FromDishka[ListTasksQuery],
        page: Annotated[int, Query(ge=1)] = 1,
        size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = 20,
        project_id: Annotated[UUID | None, Query()] = None,
        status: Annotated[TaskStatus | None, Query()] = None,
        sort: Annotated[str, Query(description=SORT_DESCRIPTION)] = "-created_at",
    ) -> PageResponse[TaskResponse]:
        result = await query.execute(
            ListTasksRequest(
                page=page, size=size, project_id=project_id, status=status, sort=sort
            )
        )
        return to_page_response(result, TaskResponse)

    return router
```

`src/modules/tasks/presentation/http/controllers/get_task.py` :

```python
"""GET /tasks/{task_id}."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.tasks.application.queries import GetTaskByIdQuery, GetTaskByIdRequest
from modules.tasks.presentation.http.schemas import TaskResponse


def create_get_task_router() -> APIRouter:
    router = APIRouter()

    @router.get(
        "/tasks/{task_id}",
        response_model=TaskResponse,
        responses=error_responses(HTTPStatus.NOT_FOUND),
        summary="Get a task",
    )
    @inject
    async def get_task(
        task_id: UUID, query: FromDishka[GetTaskByIdQuery]
    ) -> TaskResponse:
        task = await query.execute(GetTaskByIdRequest(task_id=task_id))
        return TaskResponse.model_validate(task, from_attributes=True)

    return router
```

`src/modules/tasks/presentation/http/controllers/update_task.py` :

```python
"""PATCH /tasks/{task_id}."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.tasks.application.commands import UpdateTaskCommand, UpdateTaskRequest
from modules.tasks.presentation.http.schemas import TaskResponse, UpdateTaskBody


def create_update_task_router() -> APIRouter:
    router = APIRouter()

    @router.patch(
        "/tasks/{task_id}",
        response_model=TaskResponse,
        responses=error_responses(
            HTTPStatus.NOT_FOUND, HTTPStatus.CONFLICT, HTTPStatus.UNPROCESSABLE_CONTENT
        ),
        summary="Update an open task",
    )
    @inject
    async def update_task(
        task_id: UUID, body: UpdateTaskBody, command: FromDishka[UpdateTaskCommand]
    ) -> TaskResponse:
        task = await command.execute(
            UpdateTaskRequest(
                task_id=task_id, title=body.title, description=body.description
            )
        )
        return TaskResponse.model_validate(task, from_attributes=True)

    return router
```

`src/modules/tasks/presentation/http/controllers/change_task_status.py` :

```python
"""PATCH /tasks/{task_id}/status."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.tasks.application.commands import (
    ChangeTaskStatusCommand,
    ChangeTaskStatusRequest,
)
from modules.tasks.presentation.http.schemas import ChangeTaskStatusBody, TaskResponse


def create_change_task_status_router() -> APIRouter:
    router = APIRouter()

    @router.patch(
        "/tasks/{task_id}/status",
        response_model=TaskResponse,
        responses=error_responses(
            HTTPStatus.NOT_FOUND, HTTPStatus.CONFLICT, HTTPStatus.UNPROCESSABLE_CONTENT
        ),
        summary="Change the status of a task",
    )
    @inject
    async def change_task_status(
        task_id: UUID,
        body: ChangeTaskStatusBody,
        command: FromDishka[ChangeTaskStatusCommand],
    ) -> TaskResponse:
        task = await command.execute(
            ChangeTaskStatusRequest(task_id=task_id, status=body.status)
        )
        return TaskResponse.model_validate(task, from_attributes=True)

    return router
```

`src/modules/tasks/presentation/http/controllers/delete_task.py` :

```python
"""DELETE /tasks/{task_id}."""

from http import HTTPStatus
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter

from core.presentation.http.errors import error_responses
from modules.tasks.application.commands import DeleteTaskCommand, DeleteTaskRequest


def create_delete_task_router() -> APIRouter:
    router = APIRouter()

    @router.delete(
        "/tasks/{task_id}",
        status_code=HTTPStatus.NO_CONTENT,
        responses=error_responses(HTTPStatus.NOT_FOUND),
        summary="Delete a task",
    )
    @inject
    async def delete_task(
        task_id: UUID, command: FromDishka[DeleteTaskCommand]
    ) -> None:
        await command.execute(DeleteTaskRequest(task_id=task_id))

    return router
```

`src/modules/tasks/presentation/http/controllers/__init__.py` :

```python
from .change_task_status import create_change_task_status_router
from .create_task import create_create_task_router
from .delete_task import create_delete_task_router
from .get_task import create_get_task_router
from .list_tasks import create_list_tasks_router
from .update_task import create_update_task_router

__all__ = [
    "create_change_task_status_router",
    "create_create_task_router",
    "create_delete_task_router",
    "create_get_task_router",
    "create_list_tasks_router",
    "create_update_task_router",
]
```

`src/modules/tasks/presentation/http/router.py` :

```python
"""HTTP router of the tasks module."""

from fastapi import APIRouter

from modules.tasks.presentation.http.controllers import (
    create_change_task_status_router,
    create_create_task_router,
    create_delete_task_router,
    create_get_task_router,
    create_list_tasks_router,
    create_update_task_router,
)


def create_tasks_router() -> APIRouter:
    router = APIRouter(tags=["Tasks"])
    for sub_router in (
        create_create_task_router(),
        create_list_tasks_router(),
        create_get_task_router(),
        create_update_task_router(),
        create_change_task_status_router(),
        create_delete_task_router(),
    ):
        router.include_router(sub_router)
    return router
```

Dans `src/app/routers.py`, ajouter l'import et le routeur :

```python
from modules.projects.presentation.http.router import create_projects_router
from modules.tasks.presentation.http.router import create_tasks_router


def create_api_v1_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    router.include_router(create_projects_router())
    router.include_router(create_tasks_router())
    return router
```

- [ ] **Step 4: Vérifier le succès**

Run: `uv run pytest -v`
Expected: tous les tests passent.

- [ ] **Step 5: Lint et commit**

```bash
make format && make lint
git add src/modules/tasks src/app tests/integration/tasks
git commit -m "feat(tasks): expose the tasks HTTP API" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 18: Contrats d'architecture (import-linter)

**Files:**
- Modify: `pyproject.toml` (`[tool.importlinter]`), `Makefile` (cible `lint`)

**Interfaces:**
- Consumes: tout le code de `src/`.
- Produces: `make lint` échoue si `core` importe `app`/`modules`, si un module importe `app`, si les couches sont violées dans `core`, `modules.projects` ou `modules.tasks`, si `projects` importe `tasks`, ou si `tasks` importe `projects` ailleurs que via `modules.projects.public`.

- [ ] **Step 1: Ajouter les contrats à la fin de `pyproject.toml`**

```toml
[tool.importlinter]
root_packages = ["app", "core", "modules"]

[[tool.importlinter.contracts]]
name = "core depends on neither app nor modules"
type = "forbidden"
source_modules = ["core"]
forbidden_modules = ["app", "modules"]

[[tool.importlinter.contracts]]
name = "modules do not depend on app"
type = "forbidden"
source_modules = ["modules"]
forbidden_modules = ["app"]

[[tool.importlinter.contracts]]
name = "Layers inside core and every module"
type = "layers"
containers = ["core", "modules.projects", "modules.tasks"]
layers = ["presentation | infrastructure", "application", "domain"]

[[tool.importlinter.contracts]]
name = "projects does not depend on tasks"
type = "forbidden"
source_modules = ["modules.projects"]
forbidden_modules = ["modules.tasks"]

[[tool.importlinter.contracts]]
name = "tasks only uses the public API of projects"
type = "forbidden"
source_modules = ["modules.tasks"]
forbidden_modules = [
    "modules.projects.application",
    "modules.projects.domain",
    "modules.projects.infrastructure",
    "modules.projects.presentation",
    "modules.projects.provider",
]
allow_indirect_imports = true
```

- [ ] **Step 2: Ajouter import-linter à la cible `lint` du `Makefile`** (tabulation)

```make
lint: ## Run static checks
	$(UV) ruff format --check
	$(UV) ruff check
	$(UV) mypy
	$(UV) slotscheck src
	$(UV) lint-imports
```

- [ ] **Step 3: Vérifier que les contrats sont respectés**

Run: `uv run lint-imports`
Expected: `Contracts: 5 kept, 0 broken.`

- [ ] **Step 4: Vérifier qu'une violation est détectée, puis l'annuler**

```bash
printf '\nfrom modules.projects.domain.entities import Project  # noqa: F401\n' >> src/modules/tasks/domain/enums.py
uv run lint-imports; echo "exit=$?"
git checkout src/modules/tasks/domain/enums.py
uv run lint-imports
```

Expected : le premier appel affiche `tasks only uses the public API of projects BROKEN` et `exit=1` ; après `git checkout`, `Contracts: 5 kept, 0 broken.`

- [ ] **Step 5: Lint et commit**

```bash
make lint
git add pyproject.toml Makefile
git commit -m "chore: enforce architecture boundaries with import-linter" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 19: Docker, Compose et CI

**Files:**
- Create: `Dockerfile`, `.dockerignore`, `docker-compose.yaml`, `.github/workflows/ci.yaml`

**Interfaces:**
- Consumes: `create_app` (Task 8), Alembic (Task 9), `make lint` / `make test`.
- Produces: image non-root écoutant sur 8000 avec healthcheck ; `docker compose up -d --build` démarre `db` + `api` (migrations au démarrage, reload sur `./src`) sans `.env` ; CI GitHub avec jobs `lint`, `test`, `docker`.

- [ ] **Step 1: Créer `Dockerfile`**

```dockerfile
# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project
COPY README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

FROM python:3.13-slim-bookworm AS runtime
ARG APP_UID=10001
ARG APP_GID=10001
RUN groupadd --gid "${APP_GID}" app \
    && useradd --uid "${APP_UID}" --gid "${APP_GID}" --no-create-home --shell /usr/sbin/nologin app
WORKDIR /app
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --chown=app:app pyproject.toml ./
COPY --chown=app:app migrations ./migrations
USER app
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status != 200)"]
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Créer `.dockerignore`**

```gitignore
.git
.github
.venv
.env
**/__pycache__
.mypy_cache
.pytest_cache
.ruff_cache
.coverage*
htmlcov
docs
tests
```

- [ ] **Step 3: Créer `docker-compose.yaml`**

```yaml
name: fastapi-ddd-template

services:
  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_USER: ${DATABASE__USER:-postgres}
      POSTGRES_PASSWORD: ${DATABASE__PASSWORD:-postgres}
      POSTGRES_DB: ${DATABASE__NAME:-app}
    ports:
      - "${DATABASE__PORT:-5432}:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10

  api:
    build: .
    env_file:
      - path: .env
        required: false
    environment:
      DATABASE__HOST: db
      DATABASE__PORT: 5432
      DATABASE__USER: ${DATABASE__USER:-postgres}
      DATABASE__PASSWORD: ${DATABASE__PASSWORD:-postgres}
      DATABASE__NAME: ${DATABASE__NAME:-app}
      PYTHONPATH: /app/src
    ports:
      - "8000:8000"
    volumes:
      - ./src:/app/src:ro
      - ./migrations:/app/migrations:ro
    depends_on:
      db:
        condition: service_healthy
    command: >
      sh -c "alembic upgrade head &&
             uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000
             --reload --reload-dir /app/src"

volumes:
  pgdata:
```

`PYTHONPATH=/app/src` fait primer le code monté sur le paquet installé dans l'image : le rechargement à chaud fonctionne en local, l'image seule (production) utilise le paquet installé.

- [ ] **Step 4: Créer `.github/workflows/ci.yaml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
      - run: uv sync --locked --group dev
      - run: make lint

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v6
        with:
          enable-cache: true
      - run: uv sync --locked --group dev
      - run: make test

  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start the stack
        run: docker compose up -d --build
      - name: Wait for readiness
        run: timeout 120s bash -c 'until curl -sf http://127.0.0.1:8000/health/ready; do sleep 2; done'
      - name: Smoke test the API
        run: |
          curl -sf -X POST http://127.0.0.1:8000/api/v1/projects \
            -H 'Content-Type: application/json' -d '{"name": "Smoke test"}'
          curl -sf http://127.0.0.1:8000/api/v1/projects | grep -q '"total":1'
      - name: Show logs on failure
        if: failure()
        run: docker compose logs
      - name: Tear down
        if: always()
        run: docker compose down -v
```

- [ ] **Step 5: Vérifier localement** (Docker requis ; libérer le port 5432 si une base locale l'occupe)

```bash
docker compose up -d --build
timeout 120 bash -c 'until curl -sf http://127.0.0.1:8000/health/ready; do sleep 2; done'
curl -sf -X POST http://127.0.0.1:8000/api/v1/projects -H 'Content-Type: application/json' -d '{"name": "Smoke test"}'
curl -sf http://127.0.0.1:8000/api/v1/projects | grep -q '"total":1' && echo "smoke ok"
docker inspect --format '{{.State.Health.Status}}' "$(docker compose ps -q api)"
docker compose exec api id -u
docker compose down -v
```

Expected : `{"status":"ok"}`, réponse 201 JSON du projet, `smoke ok`, `healthy`, `10001`.

- [ ] **Step 6: Commit**

```bash
git add Dockerfile .dockerignore docker-compose.yaml .github/workflows/ci.yaml
git commit -m "chore: add Docker image, Compose stack and CI workflow" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 20: README et vérification finale

**Files:**
- Modify: `README.md`

**Interfaces:**
- Consumes: l'ensemble du projet.
- Produces: documentation du boilerplate ; preuve que les critères d'acceptation du spec (section 10) sont remplis.

- [ ] **Step 1: Remplacer `README.md`** (bloc délimité par quatre backticks : copier son contenu tel quel)

````markdown
# FastAPI DDD Template

A FastAPI boilerplate for modular monoliths built with **Domain-Driven Design**,
**Clean Architecture** and **CQRS**. Two example modules, `projects` and `tasks`,
show every building block, including how modules collaborate without coupling.

## Features

- Modules split into `domain`, `application`, `infrastructure` and `presentation`,
  with dependency rules enforced by [import-linter](https://import-linter.readthedocs.io/)
- Dependency injection with [Dishka](https://dishka.readthedocs.io/): one database
  session, unit of work and event bus per request
- Async SQLAlchemy 2, PostgreSQL (psycopg 3) and Alembic
- Domain events dispatched in-process, inside the transaction that produced them
- Typed business errors rendered as [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457)
  problem details
- Pagination with whitelisted sorting, filtering and search
- Configuration from environment variables with pydantic-settings
- Unit tests without I/O and integration tests on a real PostgreSQL (testcontainers)
- Ruff, mypy (strict), slotscheck, pre-commit, Docker and GitHub Actions

## Quick start

Requirements: Python 3.13, [uv](https://docs.astral.sh/uv/) and Docker.

```bash
make install   # install dependencies and create .env from .env.example
make up        # build and start PostgreSQL and the API (migrations run on start)
```

Open <http://localhost:8000/docs>.

To run the API on your machine instead, start only the database:

```bash
docker compose up -d db
make migrate
make run
```

## Commands

| Command | Description |
|---|---|
| `make install` | Install dependencies and create `.env` |
| `make run` | Run the API locally with auto-reload |
| `make up` / `make down` | Start / stop the Docker Compose stack |
| `make migrate` | Apply migrations |
| `make migration m="message"` | Generate a migration from the ORM models |
| `make format` | Format the code and apply safe lint fixes |
| `make lint` | Ruff, mypy, slotscheck and import-linter |
| `make test` | All tests (integration tests need Docker) |
| `make test.unit` | Unit tests only |
| `make cov` | Tests with a coverage report |
| `make deps-graph` | Print the dependency injection graph (d2) |

## Configuration

Settings come from environment variables, then from `.env`. Nested settings use `__`
(`DATABASE__HOST`). See `.env.example`.

| Variable | Default | Description |
|---|---|---|
| `APP__NAME` | `FastAPI DDD Template` | OpenAPI title |
| `APP__VERSION` | `0.1.0` | OpenAPI version |
| `APP__ENVIRONMENT` | `local` | `local`, `test`, `staging` or `production` |
| `APP__DOCS_ENABLED` | `true` | Serve `/docs`, `/redoc` and `/openapi.json` |
| `DATABASE__HOST` | `localhost` | |
| `DATABASE__PORT` | `5432` | |
| `DATABASE__USER` | `postgres` | |
| `DATABASE__PASSWORD` | required | |
| `DATABASE__NAME` | `app` | |
| `DATABASE__POOL_SIZE` | `10` | |
| `DATABASE__MAX_OVERFLOW` | `10` | |
| `DATABASE__ECHO` | `false` | Log SQL statements |
| `CORS__ALLOW_ORIGINS` | `[]` | JSON list; CORS is disabled when empty |
| `LOG__LEVEL` | `INFO` | |

## Architecture

```
src/
├── app/       composition root: FastAPI factory, routers, DI providers, event wiring
├── core/      shared kernel, never imports app/ or modules/
│   ├── domain/          Entity, AggregateRoot, ValueObject, DomainEvent, errors, pagination
│   ├── application/     UnitOfWork and EventBus ports
│   ├── infrastructure/  settings, logging, SQLAlchemy repository and unit of work, event bus
│   └── presentation/    problem details, paginated responses, health probes
└── modules/
    ├── projects/
    └── tasks/
migrations/    Alembic
tests/         unit/ (no I/O), integration/ (PostgreSQL), fakes/ (in-memory doubles)
```

### Dependency rules

Checked by `make lint` (`[tool.importlinter]` in `pyproject.toml`):

1. `core` imports neither `app` nor `modules`.
2. `modules` never import `app`.
3. In `core` and in each module, `presentation` and `infrastructure` may import
   `application`, which may import `domain`; `presentation` and `infrastructure`
   never import each other.
4. A module imports another module only through its `public.py`.

### Module anatomy

```
modules/<name>/
├── public.py         the only file other modules may import
├── provider.py       Dishka provider of the module
├── domain/           entities, value objects, events, errors, enums, ports
├── application/      commands, queries, DTOs, event handlers
├── infrastructure/   ORM models, mappers, repositories, adapters to other modules
└── presentation/     HTTP schemas, one controller per endpoint, router
```

- **Commands** change state and end with `await uow.commit()`; **queries** only read.
- **Ports** are protocols declared by the module that needs them.
- Use cases return **DTOs**: entities never reach the HTTP layer.

### Unit of work and domain events

Aggregates record events with `record_event()`. Repositories track every aggregate
they add, save, delete or load by id. `UnitOfWork.commit()` then:

1. flushes pending changes;
2. publishes the recorded events: handlers run in the **same session and
   transaction** and may record new events, published in a next round
   (10 rounds at most);
3. commits. Any error rolls the whole transaction back.

Archiving a project publishes `ProjectArchived`, and `tasks` cancels the open tasks
of that project in the same transaction: if a handler fails, the project is not
archived either.

Handlers are registered in `src/app/event_handlers.py` and must never call `commit()`.
Events are not durable; to notify external systems reliably, add a transactional
outbox.

### Calls between modules

`tasks` needs to know whether a project exists and is active. It declares its own
port, `ProjectLookupPort`, implemented by an adapter calling
`modules.projects.public`. The `tasks` domain never sees a `Project`, and there is no
foreign key between the `tasks` and `projects` tables.

### Errors

Business errors inherit from a category of `core/domain/errors.py`, which decides the
HTTP status:

| Category | Status |
|---|---|
| `NotFoundError` | 404 |
| `ConflictError` | 409 |
| `BusinessRuleViolationError` | 409 |
| `DomainValidationError` | 422 |
| other `DomainError` | 400 |

Unique and foreign key violations become `ConflictError`, invalid requests return 422
and unexpected errors return a generic 500 (details only in the logs). Every error
uses `application/problem+json`:

```json
{
  "type": "about:blank",
  "title": "Conflict",
  "status": 409,
  "detail": "A project named 'Website' already exists.",
  "code": "project_name_already_exists",
  "details": {"name": "Website"}
}
```

### Pagination

List endpoints accept `page`, `size` (at most 100), `sort` (`name`, `-created_at`)
and module filters, and return `{items, total, page, size, pages}`. Repositories
declare `sortable_fields`, `filterable_fields` and `searchable_fields`; any other
field is rejected with 422.

## Testing

- `tests/unit`: domain and use cases with in-memory doubles, and the HTTP layer
  without a database.
- `tests/integration`: PostgreSQL started once per test session and migrated with
  Alembic; tables are truncated before each test. A test also checks that the
  migrations match the ORM models.

## Adding a module

1. Create `src/modules/<name>/` with the four layers.
2. Domain: value objects, aggregate (`AggregateRoot`), events, errors inheriting a
   category, repository port.
3. Application: DTO and one class per command or query; commands end with
   `uow.commit()`.
4. Infrastructure: ORM model (`UUIDPrimaryKeyMixin`, `TimestampMixin`, `Base`), mapper,
   repository (`SqlaRepository` with its whitelists).
5. Presentation: schemas, controllers, `create_<name>_router()`.
6. `provider.py`, and `public.py` for what other modules may use.
7. Wire it in `src/app/`: `providers.py`, `routers.py`, `models.py` and, if needed,
   `event_handlers.py`.
8. Add the module to the `layers` contract in `pyproject.toml`.
9. `make migration m="add <name>"`, review the generated file, `make migrate`.
10. Write unit and integration tests, then run `make lint test`.

To start from an empty template, delete `src/modules/projects` and `src/modules/tasks`
and their references in `src/app/`, `tests/`, `migrations/versions/` and
`pyproject.toml`.

## Deployment

- Build the image from the root `Dockerfile` (non-root user, port 8000, healthcheck).
- Run `alembic upgrade head` before starting a new version.
- Use `/health` for liveness and `/health/ready` for readiness.
- In production, set `APP__ENVIRONMENT=production`, `APP__DOCS_ENABLED=false` and
  explicit `CORS__ALLOW_ORIGINS`.
````

- [ ] **Step 2: Vérifier les critères d'acceptation du spec**

```bash
make clean
grep -rniE "prepaid|equation|orange|keycloak|realm|perm_|balance_type|profile_type|/sections|/rules|/reports|rule_id|section_id|report_id" \
  --exclude-dir=.git --exclude-dir=.venv --exclude-dir=superpowers --exclude=uv.lock . || echo "no previous project reference"
make lint
make test
docker compose up -d --build
timeout 120 bash -c 'until curl -sf http://127.0.0.1:8000/health/ready; do sleep 2; done'
curl -s -o /dev/null -w "%{http_code}\n" -X POST http://127.0.0.1:8000/api/v1/projects -H 'Content-Type: application/json' -d '{"name": "Acceptance"}'
docker compose down -v
```

Expected : `no previous project reference` ; lint OK ; tous les tests passent (dont `test_migrations_match_the_orm_models`, critère 5) ; readiness `{"status":"ok"}` ; `201`.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document the boilerplate" -m "Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 4: Signaler à l'utilisateur (ne rien faire automatiquement)**

- Le commit initial `c4e7784` et `docs/superpowers/` (spec et plan) mentionnent encore le projet précédent. Avant toute publication : repartir d'un historique propre (branche orpheline ou squash) et décider de conserver ou non `docs/superpowers/`.
- La branche `chore/generic-boilerplate` est prête à être intégrée (skill `superpowers:finishing-a-development-branch`).
