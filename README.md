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
