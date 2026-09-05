# Development

This document describes how to work on Gadiruta locally.

Update commands and setup instructions whenever tooling changes.

---

## Repository

Current layout:

```text
gadiruta/
    AGENTS.md
    README.md
    manage.py
    pyproject.toml
    uv.lock
    gadiruta/
    transport/
    tests/
    docs/
```

The existing Django project stays at the repository root. `frontend/` is planned.

---

## Prerequisites

Backend prerequisites:

- Git.
- Python 3.14 (verified with 3.14.0).
- uv (verified with 0.10.12) for dependencies, the lockfile, and command execution.
- PostgreSQL 15 or newer, as required by
  [Django 6.1](https://docs.djangoproject.com/en/6.1/ref/databases/#postgresql-notes).

Node.js and a frontend package manager will be selected when React is initialized.

---

## Backend

Run all commands from the repository root. `uv.lock` records exact dependency versions; Django
is pinned to 6.1.1. The CTAN adapter uses httpx and Pydantic.

```powershell
uv sync --locked
Copy-Item .env.example .env
uv run python -c 'import secrets; print(secrets.token_urlsafe(50))'
```

Put the generated key in `.env` as `DJANGO_SECRET_KEY`, and configure the PostgreSQL connection
below. Copy the example only when creating a new `.env`; preserve any existing local configuration.

```powershell
uv run --locked --env-file .env python manage.py migrate
uv run --locked --env-file .env python manage.py runserver
```

The server defaults to http://127.0.0.1:8000. The homepage/React UI is not implemented yet.
The liveness and place-search APIs do not require a database connection. Django's normal `runserver`
migration check and the scaffold's admin require a configured database.

### Checks and tests

```powershell
uv run --locked --env-file .env.example python manage.py check
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
```

The current tests run without an environment file, PostgreSQL connection, or CTAN access.
[`pytest-env`](https://github.com/pytest-dev/pytest-env) supplies the test-only secret key and debug
setting from `pyproject.toml` before Django initializes. These two values override inherited
environment values during pytest runs only. Normal application startup still requires a configured
`DJANGO_SECRET_KEY`.

In PyCharm, select the project's `.venv` interpreter and use the pytest runner with the repository
root as the working directory. Individual test modules can run directly without extra environment
variables or runner arguments. If Django support is enabled, enable **Do not use Django test
runner** and create/select a pytest run configuration; existing Django test configurations still
use Django's runner and bypass pytest configuration. Run `uv sync --locked` after dependency changes.

Database access in pytest requires an explicit `django_db` marker or `db` fixture; future database
tests must use PostgreSQL and a role that can create the test database. Supply the database
connection with `uv run --locked --env-file .env pytest` when running those tests.

Ruff handles linting, import ordering, and formatting. Use `uv run ruff format .` to format source.
mypy checks project code, including typed function bodies; untyped third-party imports are allowed
until more specific stubs are needed.

### Python docstrings

Docstrings are mandatory for every Python module (including `__init__.py`), class, named function,
and method. Tests, fixtures, helpers, private/nested definitions, constructors, and special methods
are not exempt. Use English and explain the purpose or behavioral contract; include important
side effects, failure modes, or constraints when they are not obvious from the signature. Test
docstrings should explain the scenario and expected outcome.

---

## Frontend

Stack:

- React 19.
- TypeScript.
- Vite.
- React Router.
- TanStack Query.
- react-i18next.

Document exact setup commands after frontend initialization.

Expected topics:

```text
Install dependencies
Start Vite dev server
Run TypeScript typecheck
Run ESLint
Run frontend tests
Build production bundle
```

---

## Environment variables

Do not commit `.env` files or secrets. `.env.example` contains placeholders for local development.
Settings read the process environment; `.env` is loaded only when explicitly passed to
`uv run --env-file`. Existing process environment values take precedence.

| Variable | Default / behavior |
| --- | --- |
| `DJANGO_SECRET_KEY` | Required; startup fails if missing or blank. |
| `DJANGO_DEBUG` | `false`; accepts `true` or `false`, ignoring case/outer whitespace. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1,[::1]`; comma-separated, blank entries ignored. |
| `POSTGRES_DB` | `gadiruta` |
| `POSTGRES_USER` | `gadiruta` |
| `POSTGRES_PASSWORD` | Empty; set for the configured database role. |
| `POSTGRES_HOST` | `localhost` |
| `POSTGRES_PORT` | `5432` |

The example explicitly enables debug mode. It is not production configuration. Set the real
deployment hosts, secret, and HTTPS settings before deployment. No CORS settings exist yet. CTAN
requests use the fixed HTTPS API base and consortium `2`; no API key or additional environment
variables are needed for place search.

---

## Database

Use a supported PostgreSQL server and its command-line tools. For a new local development database,
run these against that server with an administrative role (often `postgres`):

```powershell
createuser -h localhost -p 5432 -U postgres --pwprompt --createdb gadiruta
createdb -h localhost -p 5432 -U postgres --owner=gadiruta gadiruta
```

Match the port to the supported server, particularly if an older PostgreSQL service is also running.
Set `POSTGRES_PASSWORD` in `.env` to the role password, then run the migrations shown above. The
`--createdb` privilege is for local test database creation, not a production-role requirement.

To check database connectivity and applied migrations:

```powershell
uv run --locked --env-file .env python manage.py check --database default
uv run --locked --env-file .env python manage.py migrate --check
```

No transport models or synchronization commands exist yet. The original local SQLite file is not
used by the new configuration and is not automatically removed or migrated.

Do not commit local database files/dumps unless they are intentional test fixtures.

---

## CTAN fixtures

Normal automated tests must not depend on live CTAN availability.

Representative upstream responses live under:

```text
tests/fixtures/ctan/
```

The fixture README and `metadata.json` record provenance. Tests use `httpx.MockTransport` and the
default test fixture rejects live HTTPX transport calls. Cache tests isolate the place-catalogue
key; they do not require PostgreSQL or an external cache service.

When adding a fixture:

1. Capture a representative real response during discovery.
2. Remove any data that should not be committed.
3. Name the fixture by behavior/use case.
4. Document unusual provider behavior in `docs/ctan-api.md`.
5. Add tests for the corresponding normalization behavior.

Live CTAN integration tests, if added, should be clearly separated from the default deterministic test suite.

---

## API documentation

Gadiruta's own API reference is generated through Django Ninja/OpenAPI.

When adding or changing an endpoint:

- Use typed request/response schemas.
- Keep route descriptions accurate.
- Write public descriptions for API consumers; keep internal implementation and dependency details
  in developer documentation or code comments.
- Keep required route and schema docstrings useful as generated API descriptions.
- Do not manually duplicate the full endpoint contract under `docs/`.

- Interactive docs: http://127.0.0.1:8000/api/v1/docs
- OpenAPI JSON: http://127.0.0.1:8000/api/v1/openapi.json
- Application liveness: http://127.0.0.1:8000/api/v1/health
- Place-search example: http://127.0.0.1:8000/api/v1/places?q=cadiz

The place-search example contacts live CTAN on a cache miss. Query behavior and response fields
are documented in OpenAPI. The cache is process-local and resets when that process restarts.

Interactive documentation assets are supplied by the installed Ninja package through Django static
files. Development serving requires `DJANGO_DEBUG=true`; production will need static-file hosting.

---

## Localization workflow

Frontend UI supports:

- English.
- Spanish.

Expected translation files:

```text
frontend/src/i18n/en.json
frontend/src/i18n/es.json
```

When adding user-facing text:

1. Add/update the English source string.
2. Add/update the Spanish translation.
3. Use the translation key in the component.
4. Avoid literal user-facing strings in JSX.

---

## Git workflow

Before work:

```bash
git status
```

After a coherent change:

1. Run relevant tests/checks.
2. Review `git diff`.
3. Update affected docs.
4. Commit with a focused English message.

Examples:

```text
feat: add CTAN API client
feat: expose places search endpoint
feat: connect place autocomplete to API
fix: handle CTAN timeout responses
```

Avoid giant implementation commits and trivial microcommits.

---

## Documentation workflow

Update documentation as implementation changes:

```text
Feature behavior         → docs/features.md
Architecture             → docs/architecture.md
CTAN discoveries         → docs/ctan-api.md
Major decisions          → docs/decisions.md
Developer workflow       → docs/development.md
Product scope            → docs/product.md
Own API contract         → code/OpenAPI
```

Do not maintain a separate agent-session diary.
