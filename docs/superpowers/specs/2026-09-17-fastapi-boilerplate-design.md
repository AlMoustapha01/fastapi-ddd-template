# Conversion en boilerplate FastAPI DDD — Design

- **Date :** 2026-09-17
- **Statut :** validé en brainstorming, en attente de relecture du spec
- **Branche :** `chore/generic-boilerplate`

## 1. Objectif

Transformer le repo (backend d'un projet précédent : modules `auth`, `users`, `rules`, `reports`
adossés à Keycloak) en **boilerplate FastAPI générique** :

1. retirer toute mention du projet précédent (code, config, realm, migrations, tests, docs, CI) ;
2. fournir une implémentation générique qui illustre l'architecture via deux modules liés
   (`projects`, `tasks`) ;
3. corriger les problèmes identifiés (section 3).

### Hors périmètre

- Authentification / autorisation (décision : **aucune auth** ; à ajouter par projet).
- Transactional outbox, messaging externe, cache, observabilité avancée (tracing, métriques).
- Frontend.

## 2. Décisions

| Sujet | Décision |
|---|---|
| Auth | Aucune. Suppression de `auth`, `users`, Keycloak (compose, realm, config, deps). |
| Exemple | Deux modules liés : `projects` et `tasks`. |
| Communication inter-modules | Port synchrone (côté consommateur) + événements de domaine in-process. |
| Publication des événements | **Dans la transaction**, avant le commit final (atomique). |
| Configuration | `pydantic-settings` (variables d'env + `.env` optionnel). Suppression du système TOML. |
| Tests d'intégration | `testcontainers` PostgreSQL, isolation par `TRUNCATE` entre tests. |
| Approche | Refonte ciblée du core (garder les bonnes abstractions, remplacer celles qui causent les bugs). |
| Langue | Code et README en anglais. |

## 3. Problèmes identifiés et correctifs

### 3.1 Bugs reproduits

| # | Problème | Correctif |
|---|---|---|
| B1 | `/api/v1/health` et `/` répondent 401 (middleware : `/health` public, route réelle `/api/v1/health`). CI health check impossible. | Middleware d'auth supprimé ; `/health` et `/health/ready` à la racine. |
| B2 | Chaque provider fournit `Flusher` / `TransactionManager` ; Dishka garde le dernier → `SqlaUserFlusher` injecté partout, erreurs métier des autres modules jamais levées. | `Flusher` + `TransactionManager` remplacés par un unique `UnitOfWork` fourni par le core. |
| B3 | `greenlet` absent sur macOS arm64 → toute opération DB async échoue. | Dépendance `sqlalchemy[asyncio]`. |
| B4 | 48 tests en échec + 8 erreurs sur 57 (tests désynchronisés du domaine). | Suite de tests réécrite pour les nouveaux modules. |
| B5 | Second engine + pool créés dans `create_web_app` hors DI (jamais disposés), en plus de celui de Dishka. | Un seul engine, fourni par Dishka (scope APP), disposé à la fermeture du conteneur. |

### 3.2 Architecture / sécurité / qualité

| # | Problème | Correctif |
|---|---|---|
| A1 | `core` importe `modules.*` (middleware, `core/services/user_profile_service.py`). | Supprimés ; contrats **import-linter** en CI. |
| A2 | Toute exception non prévue → 503 via `error_map` par route ; `DomainErrorTranslator` renvoie `str(err)` ; `ValueError` des VO → 503. | Hiérarchie d'erreurs typées + handlers globaux (RFC 9457) ; 500 générique journalisé. `fastapi-error-map` retiré. |
| A3 | Erreurs du module `users` hors hiérarchie `DomainError`. | Module supprimé ; toutes les erreurs métier héritent de `DomainError`. |
| A4 | `order_by_field` / filtres : `getattr` arbitraire sur le modèle. Jokers `ILIKE` non échappés. | Liste blanche par repository ; échappement de `%`, `_`, `\`. |
| A5 | Détection d'unicité par recherche de mots dans le message d'`IntegrityError`. | Mapping par `sqlstate` psycopg (`23505` → `ConflictError`, `23503` → `ConflictError`). |
| A6 | `BaseRepository.delete` / `find_one_by_id` : variables potentiellement non liées dans les `except`. | Réécriture. |
| A7 | `Entity.updated_at_` non mis à jour lors des mutations de `props` (le `__setattr__` ne les voit pas). | `touch()` explicite appelé par les méthodes de mutation. |
| A8 | `User.validate()` appelé deux fois. | Disparaît avec le module ; `Entity.__init__` est le seul appelant de `validate()`. |
| A9 | Config dupliquée (`config/toml_config_manager.py` vs `src/core/config/loader.py`), hack `POSTGRES_HOST` dans un validator, secrets versionnés, CORS codé en dur (`localhost:4200`). | `pydantic-settings`, `.env.example`, CORS configurable. |
| A10 | Alembic configuré à la fois dans `alembic.ini` et `pyproject.toml`. | Config uniquement dans `pyproject.toml`. |
| A11 | Wheel n'embarque que `src/app`. | `packages = ["src/app", "src/core", "src/modules"]`. |
| A12 | Dockerfile expose/écoute 8888, compose utilise 8000 ; Dockerfile dans `config/local/`. | `Dockerfile` racine, port 8000, healthcheck. |
| A13 | Code mort : `OAuth2Provider`, `add_auth_to_routes`, `get_user_from_context`, `core/lib/http/callbacks.py`. | Supprimé. |
| A14 | Script `docker_prune.sh` (`docker system prune -a --volumes`) dans un template. | Supprimé. |
| A15 | CI appelle `/api/v1/sections/` ; `.DS_Store` versionnés ; pas de repo git. | CI réécrite ; `.gitignore` complété ; repo initialisé. |

## 4. Architecture

### 4.1 Arborescence cible

```
.
├── Dockerfile
├── docker-compose.yaml
├── .dockerignore
├── .env.example
├── Makefile
├── pyproject.toml            # deps, ruff, mypy, pytest, coverage, slotscheck, alembic, importlinter
├── README.md
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/<date>-<rev>_initial_schema.py
├── scripts/dishka/plot_dependencies_data.py
├── src/
│   ├── app/
│   │   ├── main.py            # create_app(settings=None, *providers) + entrypoint
│   │   ├── lifespan.py
│   │   ├── routers.py         # root router, /api/v1, health
│   │   ├── providers.py       # registre des providers Dishka (core + modules)
│   │   ├── event_handlers.py  # registre événement -> handlers
│   │   └── models.py          # importe tous les modèles ORM (Alembic)
│   ├── core/
│   │   ├── domain/            # entity.py, aggregate_root.py, value_object.py, events.py, errors.py
│   │   ├── application/       # unit_of_work.py, event_bus.py, pagination.py
│   │   ├── infrastructure/
│   │   │   ├── settings.py
│   │   │   ├── logging.py
│   │   │   ├── db/            # base.py, mixins.py, provider.py, repository.py, unit_of_work.py, errors.py, tracker.py
│   │   │   ├── events/        # in_process_bus.py
│   │   │   └── provider.py    # CoreProvider (settings, db, uow, bus)
│   │   └── presentation/http/ # errors.py (handlers), pagination.py (schémas), health.py
│   └── modules/
│       ├── projects/
│       └── tasks/
└── tests/
    ├── conftest.py
    ├── unit/{core,projects,tasks}/
    └── integration/{conftest.py,projects,tasks}/
```

### 4.2 Anatomie d'un module

Conserve les conventions existantes (une classe de use case par fichier, un contrôleur par
endpoint, provider par module) :

```
modules/<name>/
├── __init__.py
├── public.py                       # SEULE surface importable par d'autres modules
├── provider.py                     # Provider Dishka du module
├── domain/
│   ├── entities/  value_objects/  events.py  errors.py  enums.py
│   └── ports/                      # repository port (+ ports vers d'autres modules)
├── application/
│   ├── commands/   queries/   dto.py
│   └── event_handlers/             # (tasks uniquement)
├── infrastructure/
│   ├── models/  mappers/  repositories/
│   └── adapters/                   # (tasks : projects_lookup.py)
└── presentation/http/
    ├── router.py  schemas.py
    └── controllers/
```

### 4.3 Règles de dépendance (import-linter)

1. `core` n'importe ni `app` ni `modules`.
2. `modules` n'importe pas `app`.
3. Couches dans chaque module et dans `core` : `presentation` → `application` → `domain` ;
   `infrastructure` → `application`, `domain`. `domain` n'importe aucune autre couche.
4. Un module n'importe d'un autre module que son `public.py`
   (`modules.tasks.*` → `modules.projects.public` uniquement, et réciproquement).

Les contrats sont déclarés dans `[tool.importlinter]` et exécutés par `make lint` et la CI.

## 5. Core

### 5.1 Domaine

- `ValueObject` : conservé tel quel (dataclass frozen/slots, repr contrôlé).
- `Entity[TId, TProps]` : conservé ; identité immuable, égalité par id, `validate()` abstrait
  appelé une fois dans `__init__`. Remplacement du `__setattr__` qui modifiait `updated_at_` par
  une méthode `touch()` appelée explicitement par les mutations.
- `AggregateRoot(Entity)` : `_events: list[DomainEvent]`, `record(event)`, `pull_events() -> list`.
- `DomainEvent` : conservé (frozen dataclass, `event_id` UUID7, `occurred_at` UTC).
- `errors.py` :

| Classe | HTTP |
|---|---|
| `DomainError` (base : `message`, `code`, `details`) | 400 |
| `NotFoundError` | 404 |
| `ConflictError` | 409 |
| `BusinessRuleViolationError` | 409 |
| `DomainValidationError` | 422 |

  Les value objects lèvent `DomainValidationError` (plus de `ValueError`).

### 5.2 Application

- `UnitOfWork` (Protocol) : `async commit()`, `async rollback()`.
- `EventBus` (Protocol) : `async publish(event: DomainEvent)`.
- `EventHandler[E]` (Protocol) : `async handle(event: E)`.
- `pagination.py` : `Page[T]` (items, total, page, size, pages), `PageParams`, `SortParams`
  (field, direction), types de filtres (repris de `paginated.py`, simplifiés).

### 5.3 Infrastructure DB

- `Base` SQLAlchemy avec `MetaData(naming_convention=...)` (noms de contraintes déterministes).
- Mixins `UUIDPrimaryKeyMixin`, `TimestampMixin` (conservés).
- `DatabaseProvider` : `AsyncEngine` (APP, disposé à la fermeture), `async_sessionmaker` (APP),
  `AsyncSession` (REQUEST).
- `AggregateTracker` (REQUEST) : ensemble des agrégats vus pendant la requête.
- `SqlaRepository[TEntity, TModel]` : `add`, `save` (merge), `delete`, `get_by_id`, `list_page`.
  Enregistre les agrégats dans le tracker. Tri/filtres limités à `sortable_fields` /
  `filterable_fields` déclarés par chaque repository ; champ inconnu → `DomainValidationError`.
  `SQLAlchemyError` non-intégrité → laissée remonter (500 via handler global).
- Suppression d'un agrégat : l'agrégat reste référencé par le tracker, ses événements
  (`ProjectDeleted`) sont donc publiés au commit.
- `SqlaUnitOfWork.commit()` (au plus `MAX_EVENT_ROUNDS` tours de dispatch) :

```
for _ in range(MAX_EVENT_ROUNDS):          # MAX_EVENT_ROUNDS = 10
    events = tracker.pull_all_events()
    if not events: break
    for event in events: await bus.publish(event)   # handlers utilisent la même session
else:
    raise RuntimeError("Domain event dispatch did not converge")
try:
    await session.flush(); await session.commit()
except IntegrityError as err:
    await session.rollback()
    raise map_integrity_error(err) from err     # sqlstate 23505/23503 -> ConflictError
```

  Les handlers ne doivent jamais appeler `commit()` (documenté).

- `InProcessEventBus` : reçoit l'`AsyncContainer` de la requête et un registre
  `Mapping[type[DomainEvent], Sequence[type[EventHandler]]]` ; résout chaque handler via le
  conteneur et l'exécute séquentiellement. (Vérifié : Dishka injecte `AsyncContainer` du scope
  courant.)

### 5.4 Settings

`Settings(BaseSettings)`, `env_nested_delimiter="__"`, `env_file=".env"` (optionnel) :

| Groupe | Variables |
|---|---|
| `app` | `APP__NAME`, `APP__VERSION`, `APP__ENVIRONMENT` (`local`/`test`/`staging`/`production`), `APP__DOCS_ENABLED` |
| `database` | `DATABASE__HOST`, `__PORT`, `__USER`, `__PASSWORD` (`SecretStr`), `__NAME`, `__DRIVER` (`psycopg`), `__POOL_SIZE`, `__MAX_OVERFLOW`, `__ECHO`, `__ECHO_POOL` ; propriété `url` |
| `cors` | `CORS__ALLOW_ORIGINS` (liste JSON, vide par défaut → pas de middleware CORS) |
| `log` | `LOG__LEVEL` |

`create_app(settings=None)` : charge `Settings()` si non fourni (les tests injectent les leurs).

### 5.5 Présentation HTTP

- Handlers globaux enregistrés dans `create_app` :
  - `DomainError` et sous-classes → `application/problem+json`
    `{type, title, status, detail, code, details}` ;
  - `RequestValidationError` → 422 au même format (`errors` = détails Pydantic) ;
  - `Exception` → 500 `{"title": "Internal Server Error"}`, stacktrace uniquement dans les logs.
- `GET /health` → `{"status": "ok"}` ; `GET /health/ready` → `SELECT 1`, 200 ou 503.
- `GET /` → redirection `/docs` (si docs activées).
- `default_response_class` par défaut de FastAPI (retrait d'`ORJSONResponse`).

## 6. Modules

### 6.1 `projects`

**Domaine**

- `Project(AggregateRoot[ProjectId, ProjectProps])`
  - `ProjectId(UUID)`, `ProjectName` (strip, 1..100), `ProjectDescription` (≤ 2000, défaut `""`),
    `ProjectStatus` (`ACTIVE`, `ARCHIVED`).
  - `create(name, description)` → `ProjectCreated(project_id, name)`.
  - `rename(name)`, `change_description(description)` → `touch()` ; interdit si archivé
    (`ProjectArchivedError`, `BusinessRuleViolationError`).
  - `archive()` → `ProjectArchived(project_id)` ; déjà archivé → `ProjectAlreadyArchivedError`.
  - `mark_deleted()` → `ProjectDeleted(project_id)`.
- Erreurs : `ProjectNotFoundError` (404), `ProjectNameAlreadyExistsError` (409),
  `ProjectAlreadyArchivedError`, `ProjectArchivedError` (409).
- Port : `ProjectRepositoryPort` (`add`, `save`, `delete`, `get_by_id`, `exists_by_name`,
  `list_page`).

**Application**

| Use case | Entrée | Sortie |
|---|---|---|
| `CreateProjectCommand` | name, description | `ProjectDTO` |
| `UpdateProjectCommand` | id, name?, description? | `ProjectDTO` |
| `ArchiveProjectCommand` | id | `ProjectDTO` |
| `DeleteProjectCommand` | id | `None` |
| `GetProjectByIdQuery` | id | `ProjectDTO` |
| `ListProjectsQuery` | page, size, status?, search?, sort | `Page[ProjectDTO]` |

Unicité du nom : vérification applicative (`exists_by_name`) pour un message clair + contrainte
unique en base (mappée en `ConflictError` en cas de course).

**Surface publique (`public.py`)**

```python
@dataclass(frozen=True, slots=True)
class ProjectSummary:
    id: UUID
    name: str
    is_active: bool

class ProjectsPublicApi:
    async def get_summary(self, project_id: UUID) -> ProjectSummary | None: ...

# ré-export : ProjectArchived, ProjectDeleted, ProjectsPublicApi, ProjectSummary
```

**Persistance** : table `projects` (`id` uuid PK, `name` varchar(100) unique, `description` text
not null default `''`, `status` varchar(20) + CHECK, `created_at`, `updated_at`).

### 6.2 `tasks`

**Domaine**

- `Task(AggregateRoot[TaskId, TaskProps])`
  - `project_id: UUID` (référence, pas de FK inter-module), `TaskTitle` (strip, 1..200),
    `TaskDescription` (≤ 5000), `TaskStatus` (`TODO`, `IN_PROGRESS`, `DONE`, `CANCELLED`).
  - `create(project_id, title, description)`.
  - `rename`, `change_description` → interdits si statut terminal (`DONE`, `CANCELLED`).
  - Transitions :

| De \ Vers | IN_PROGRESS | DONE | CANCELLED |
|---|---|---|---|
| TODO | ✅ `start` | ✅ `complete` | ✅ `cancel` |
| IN_PROGRESS | — | ✅ `complete` | ✅ `cancel` |
| DONE / CANCELLED | ❌ | ❌ | ❌ |

    Transition invalide → `InvalidTaskTransitionError` (409).
  - `change_status(target)` délègue à `start`/`complete`/`cancel`.
- Erreurs : `TaskNotFoundError` (404), `InvalidTaskTransitionError` (409),
  `TaskClosedError` (409), `TaskProjectNotFoundError` (404), `TaskProjectArchivedError` (409)
  (noms distincts des erreurs du module `projects` pour éviter toute confusion).
- Ports :
  - `TaskRepositoryPort` (`add`, `save`, `delete`, `get_by_id`, `list_page`,
    `list_open_by_project`, `delete_by_project`) ;
  - `ProjectLookupPort` : `async get(project_id) -> ProjectRef | None` (`ProjectRef` : id,
    is_active — modèle propre à `tasks`, pas celui de `projects`).

**Application**

| Use case | Entrée | Sortie |
|---|---|---|
| `CreateTaskCommand` | project_id, title, description | `TaskDTO` |
| `UpdateTaskCommand` | id, title?, description? | `TaskDTO` |
| `ChangeTaskStatusCommand` | id, status | `TaskDTO` |
| `DeleteTaskCommand` | id | `None` |
| `GetTaskByIdQuery` | id | `TaskDTO` |
| `ListTasksQuery` | page, size, project_id?, status?, sort | `Page[TaskDTO]` |

`CreateTaskCommand` : `ProjectLookupPort.get()` → `None` ⇒ `TaskProjectNotFoundError`,
`is_active=False` ⇒ `TaskProjectArchivedError`.

**Handlers d'événements**

- `CancelTasksOnProjectArchived` : `list_open_by_project` → `cancel()` → `save`.
- `DeleteTasksOnProjectDeleted` : `delete_by_project(project_id)`.

**Adaptateur** : `ProjectsModuleLookup(ProjectLookupPort)` dépend de `ProjectsPublicApi`
(injecté par Dishka) et traduit `ProjectSummary` → `ProjectRef`.

**Persistance** : table `tasks` (`id`, `project_id` uuid not null indexé, `title` varchar(200),
`description` text, `status` varchar(20) + CHECK, `created_at`, `updated_at`) ; index
`(project_id, status)`.

### 6.3 API HTTP (`/api/v1`)

| Méthode | Chemin | Succès | Erreurs |
|---|---|---|---|
| POST | `/projects` | 201 | 409 nom existant, 422 |
| GET | `/projects` | 200 | 422 (tri/filtre invalide) |
| GET | `/projects/{project_id}` | 200 | 404 |
| PATCH | `/projects/{project_id}` | 200 | 404, 409 (nom / archivé), 422 |
| POST | `/projects/{project_id}/archive` | 200 | 404, 409 |
| DELETE | `/projects/{project_id}` | 204 | 404 |
| POST | `/tasks` | 201 | 404 projet, 409 projet archivé, 422 |
| GET | `/tasks` | 200 | 422 |
| GET | `/tasks/{task_id}` | 200 | 404 |
| PATCH | `/tasks/{task_id}` | 200 | 404, 409 (tâche close), 422 |
| PATCH | `/tasks/{task_id}/status` | 200 | 404, 409 transition, 422 |
| DELETE | `/tasks/{task_id}` | 204 | 404 |

Pagination en query : `page` (≥ 1, défaut 1), `size` (1..100, défaut 20), `sort`
(`name`, `-created_at`…), filtres spécifiques. Réponse paginée :
`{items, total, page, size, pages}`.

## 7. Outillage

### 7.1 Dépendances

- Retirées : `python-jose`, `openpyxl`, `python-slugify`, `fastapi-error-map`,
  `alembic-postgresql-enum`, `keyof` (+ plugin mypy), `uvloop`, `httpx` (runtime),
  `line-profiler`.
- Runtime : `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `sqlalchemy[asyncio]`,
  `psycopg[binary]`, `alembic`, `dishka`, `uuid-utils`.
- Dev/test : `ruff`, `mypy`, `slotscheck`, `import-linter`, `pre-commit`, `pytest`,
  `pytest-asyncio`, `httpx`, `testcontainers[postgres]`, `coverage`.
- `uv.lock` régénéré ; `pyproject` : nom `fastapi-ddd-template`, description réelle,
  wheel `src/app`, `src/core`, `src/modules`.

### 7.2 Docker

- `Dockerfile` racine multi-stage (uv builder `--no-editable --no-dev`, image finale slim,
  utilisateur non-root, `EXPOSE 8000`, `HEALTHCHECK` sur `/health`,
  `CMD uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000`).
- `docker-compose.yaml` : `db` (postgres:17-alpine, volume, healthcheck) ; `api` (build local,
  valeurs par défaut de dev dans `environment`, `env_file` `.env` optionnel
  (`required: false`), `DATABASE__HOST=db`, `alembic upgrade head` puis uvicorn `--reload`,
  montage `./src`). `docker compose up` fonctionne sans créer de `.env`.
- `.dockerignore`.

### 7.3 Makefile

`install`, `run`, `up`, `down`, `migrate`, `migration m="..."`, `format`, `lint`
(ruff check + format --check, mypy, slotscheck, lint-imports), `test`, `test.unit`, `cov`,
`clean`, `deps-graph`. Toutes les commandes via `uv run`.

### 7.4 CI (`.github/workflows/ci.yaml`)

- `lint` : `uv sync --locked` + `make lint`.
- `test` : `make test` (testcontainers, Docker disponible sur `ubuntu-latest`).
- `docker` : `docker compose up -d --build`, attente
  `/health/ready`, `POST` puis `GET /api/v1/projects`, logs en cas d'échec, `down -v`.

### 7.5 Pre-commit

Hook local `make lint` (conservé).

## 8. Tests

- **Unitaires (`tests/unit/`)** — sans Docker :
  - core : `Entity` (égalité, id immuable, `touch`), `AggregateRoot` (événements),
    `SqlaUnitOfWork` avec session factice (ordre dispatch → flush → commit, convergence,
    mapping `IntegrityError`), `InProcessEventBus`, handlers d'erreurs HTTP ;
  - projects / tasks : value objects, agrégats (règles, transitions, événements), use cases
    avec fakes en mémoire (`InMemoryProjectRepository`, `FakeUnitOfWork`,
    `FakeProjectLookup`), handlers d'événements.
- **Intégration (`tests/integration/`, marqueur `integration`)** :
  - fixture session : `PostgresContainer("postgres:17-alpine", driver="psycopg")`,
    `alembic upgrade head` ;
  - fixture par test : `TRUNCATE projects, tasks` ;
  - client `httpx.AsyncClient(transport=ASGITransport(app))` avec `create_app(test_settings)` ;
  - couvre : CRUD projects/tasks, pagination/tri/filtres (+ champ interdit → 422), conflit de
    nom (vérif applicative et contrainte), 404, transitions invalides, création de tâche sur
    projet inexistant/archivé, **archivage → tâches ouvertes annulées (DONE inchangées)**,
    **suppression → tâches supprimées**, rollback complet si un handler échoue (registre de
    handlers surchargé via un provider de test passé à `create_app`), `/health/ready`.
- `make test` = tout ; `make test.unit` = `-m "not integration"`.

## 9. Documentation et nettoyage

- `README.md` (anglais) : présentation, stack, démarrage rapide, configuration, architecture et
  règles de dépendance, anatomie d'un module, UoW et événements (limites + outbox comme évolution),
  gestion d'erreurs, tests, checklist « ajouter un module », commandes Make.
- Supprimés : `AUTHENTICATION.md`, `config/` (dont realm et `.secrets.toml`),
  `src/modules/{auth,users,rules,reports}`, `src/core/{config,lib,security,services}` (remplacés),
  anciennes migrations, anciens tests, `scripts/makefile/`, `alembic.ini`, `.DS_Store`.
- `.gitignore` : `.env`, `.coverage*`, `htmlcov/`, `.DS_Store`, caches outils.
- **Avant tout push public** : le commit initial (`c4e7784`) contient l'état du projet précédent
  (noms, realm, client secret local). Repartir d'un historique propre (branche orpheline /
  squash) avant publication.

## 10. Critères d'acceptation

1. `grep -rniE "prepaid|equation|orange|keycloak|realm|perm_|balance_type|profile_type|/sections|/rules|/reports|rule_id|section_id|report_id"`
   sur le repo (hors `uv.lock`, `.git`, `.venv`, `docs/superpowers/`) ne renvoie rien.
2. `make lint` passe (ruff, mypy strict, slotscheck, import-linter).
3. `make test` passe (unitaires + intégration testcontainers).
4. `docker compose up --build` : `/health/ready` = 200, `POST /api/v1/projects` = 201.
5. `alembic upgrade head` puis `alembic check` : aucune différence modèle/migration.

## 11. Révisions après la revue de code (2026-09-17)

Décisions validées après la revue finale de l'implémentation :

1. **Repository (remplace « `save` (merge) » du §5.3).** `session.merge()` relisait la ligne
   et recopiait toutes les colonnes : une ligne supprimée par une requête concurrente était
   réinsérée et les modifications concurrentes écrasées. Le repository garde désormais les
   modèles qu'il ajoute ou charge pendant la requête ; `save` écrit l'agrégat sur ce modèle,
   `delete` utilise `session.delete` (ou `expunge` pour un modèle non encore inséré). Un
   agrégat non chargé par le repository lève `UntrackedAggregateError`.
2. **Verrou optimiste.** `VersionMixin` (`version_id_col` SQLAlchemy) sur `projects` et
   `tasks` ; `StaleDataError` → `ConflictError` (`concurrent_modification`, 409).
3. **Course création de tâche / archivage ou suppression (§6.2).** `CreateTaskCommand` pose
   un verrou `FOR SHARE` sur le projet via `ProjectLookupPort.get(..., lock=True)` →
   `ProjectsPublicApi.get_summary(..., lock=True)` → `get_by_id(..., lock=True)`.
4. **Mineurs.** Exactement `MAX_EVENT_ROUNDS` tours de dispatch autorisés ; handler
   `HTTPException` robuste (statuts sans corps, `detail` structuré, codes non standard) ;
   `CORS__ALLOW_CREDENTIALS` configurable (faux par défaut) ; Postgres de Compose lié à
   `127.0.0.1` ; venv de l'image en lecture seule pour l'utilisateur runtime ; CI avec
   `permissions: contents: read` et groupe de concurrence ; README complété.
