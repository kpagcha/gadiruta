# Development

This document contains the commands and conventions needed to work on Gadiruta locally. Keep implementation details in code/configuration unless developers genuinely need them here.

## Prerequisites

- Git.
- Python 3.14.
- [uv](https://docs.astral.sh/uv/).
- Docker Desktop with Docker Compose V2.
- PostgreSQL 15+; Compose currently uses PostgreSQL 16.
- Node.js 24 and npm 11.

## Quick start

Run from the repository root in PowerShell.

```powershell
uv sync --locked
Copy-Item .env.example .env
uv run --locked python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Put the generated value in `.env` as `DJANGO_SECRET_KEY`, then set the local PostgreSQL and pgAdmin passwords.

Start local services:

```powershell
docker compose up --detach
uv run --locked --env-file .env python manage.py migrate
```

Optional admin account:

```powershell
uv run --locked --env-file .env python manage.py createsuperuser
```

Start Django:

```powershell
uv run --locked --env-file .env python manage.py runserver
```

Start the frontend in another terminal:

```powershell
npm --prefix frontend ci
npm --prefix frontend run dev
```

Open:

- Web app: http://127.0.0.1:5173
- API: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/api/v1/docs
- pgAdmin: http://127.0.0.1:5050

Vite proxies `/api/` to Django on port 8000.

## Database

`compose.yaml` provides PostgreSQL and pgAdmin for local development. Named volumes preserve data across normal restarts.

```powershell
docker compose up --detach
docker compose ps
docker compose down
```

Do not run `docker compose down --volumes` unless you intend to delete local database and pgAdmin state.

To verify connectivity/migrations:

```powershell
uv run --locked --env-file .env python manage.py check --database default
uv run --locked --env-file .env python manage.py migrate --check
```

Tests use PostgreSQL; the configured development role must be able to create the test database.

## Backend commands

```powershell
uv run --locked --env-file .env python manage.py check
uv run --locked --env-file .env python manage.py makemigrations --check --dry-run
uv run --locked --env-file .env pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
```

To format Python:

```powershell
uv run --locked ruff format .
```

Normal tests must not make live CTAN requests.

## Frontend commands

```powershell
npm --prefix frontend ci
npm --prefix frontend run dev
npm --prefix frontend run build
npm --prefix frontend run preview
npm --prefix frontend run format
```

Production build output goes to ignored `frontend/dist/`.

The frontend uses React, TypeScript, Vite, Tailwind CSS, Lucide React, React Router, TanStack Query, and react-i18next.

## Environment variables

`.env` is private and must not be committed. Settings read the process environment; local commands normally load `.env` with `uv run --env-file .env`.

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Required Django signing secret. |
| `DJANGO_DEBUG` | Local/debug mode flag. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts. |
| `POSTGRES_DB` | PostgreSQL database name. |
| `POSTGRES_USER` | PostgreSQL role. |
| `POSTGRES_PASSWORD` | PostgreSQL role password. |
| `POSTGRES_HOST` | PostgreSQL host. |
| `POSTGRES_PORT` | PostgreSQL port. |
| `PGADMIN_DEFAULT_EMAIL` | Local pgAdmin login. |
| `PGADMIN_DEFAULT_PASSWORD` | Local pgAdmin password. |
| `GADIRUTA_PLACE_PROVIDER` | Current place provider selection; CTAN is implemented. |
| `GADIRUTA_DIRECT_JOURNEY_PROVIDER` | Current direct-journey provider selection; existing CTAN path is transitional until GTFS migration. |

Do not treat `.env.example` as production configuration.

## Provider and data fixtures

Captured CTAN REST fixtures live under `tests/fixtures/ctan/`. Use them for parsing/error behavior rather than live requests.

When adding an upstream fixture:

1. capture a representative response during discovery;
2. remove anything unsuitable for the repository;
3. record request/provenance metadata;
4. document meaningful provider quirks in `docs/ctan-api.md`;
5. add deterministic tests.

For GTFS work, prefer small representative fixture feeds that exercise importer/query behavior without requiring the full live feed in the normal test suite.

The GTFS importer should eventually be runnable as a management command so it can be tested manually and scheduled without adding Celery.

## Inspect the CTAN GTFS feed

The read-only inspection command downloads CTAN's current unified archive, validates its expected
ZIP/CSV structure, and reports its checksum, table counts, agencies, route types, and service-date
range. It does not write to PostgreSQL:

```powershell
uv run --locked --env-file .env python manage.py inspect_gtfs
```

For repeatable local inspection without a network request, pass a downloaded archive explicitly:

```powershell
uv run --locked --env-file .env python manage.py inspect_gtfs --file path\to\gtfs.zip
```

## Import the CTAN GTFS feed

The importer persists a new immutable dataset and atomically makes it active only after all required
tables and schedule-critical references validate. It is safe to run repeatedly: an already imported
archive checksum is reported as an idempotent no-op.

```powershell
uv run --locked --env-file .env python manage.py import_gtfs
```

Use a local archive to repeat a known import without a network request:

```powershell
uv run --locked --env-file .env python manage.py import_gtfs --file path\to\gtfs.zip
```

The command is designed for a future cron or scheduler invocation; do not add Celery or Redis solely
for this import.

After a CTAN import, refresh the population-centre-to-physical-stop crosswalk used by future local
direct-journey queries:

```powershell
uv run --locked --env-file .env python manage.py link_ctan_gtfs_places
```

The command reads CTAN's place, municipality, and physical-stop catalogues, then replaces links only
for the active GTFS dataset. It refuses an empty crosswalk and leaves existing links unchanged in
that case.

## API documentation

Django Ninja/OpenAPI is the canonical endpoint reference.

- Interactive docs: http://127.0.0.1:8000/api/v1/docs
- OpenAPI JSON: http://127.0.0.1:8000/api/v1/openapi.json
- Health: http://127.0.0.1:8000/api/v1/health
- Place search: http://127.0.0.1:8000/api/v1/places?q=cadiz
- Direct journeys: http://127.0.0.1:8000/api/v1/journeys/direct

Keep global data attribution/independence text in the top-level API description rather than repeating it on every endpoint.

## Localization

Translation files:

```text
frontend/src/i18n/en.json
frontend/src/i18n/es.json
```

When adding user-facing text, update both languages and reference the translation key from the component. Avoid literal UI strings in JSX.

## Python documentation

Follow the project's configured lint/type rules. Public modules/classes/functions should have useful English docstrings describing purpose and non-obvious behavior; do not duplicate implementation details mechanically.

## Git hooks and workflow

Install the repository hooks once per clone:

```powershell
uv run --locked pre-commit install --install-hooks
```

Useful full checks:

```powershell
uv run --locked pre-commit run --all-files
uv run --locked pre-commit run --hook-stage pre-push --all-files
```

Before a coherent change:

```powershell
git status
```

Before committing, run relevant checks, review `git diff`, and update affected docs. Use focused Conventional Commit-style English messages such as:

```text
feat: import CTAN GTFS data
fix: preserve overnight GTFS stop times
docs: streamline project documentation
```

Avoid giant implementation commits and trivial microcommits.
