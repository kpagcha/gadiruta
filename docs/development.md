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
    frontend/
    tests/
    docs/
```

The existing Django project stays at the repository root; the React application lives in `frontend/`.

---

## Prerequisites

Backend prerequisites:

- Git.
- Python 3.14 (verified with 3.14.0).
- uv (verified with 0.10.12) for dependencies, the lockfile, and command execution.
- PostgreSQL 15 or newer, as required by
  [Django 6.1](https://docs.djangoproject.com/en/6.1/ref/databases/#postgresql-notes).

Frontend prerequisites: Node.js 24 (24.11.1 or newer within that major) and npm 11.

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

The API server defaults to http://127.0.0.1:8000. Start the frontend separately as described below.
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
- Tailwind CSS 4 through the Vite plugin.
- Lucide React for interface icons.
- React Router.
- TanStack Query.
- react-i18next.

From the repository root, install the versions recorded in `frontend/package-lock.json`:

```powershell
npm --prefix frontend ci
npm --prefix frontend run dev
```

Open http://127.0.0.1:5173 with Django running on port 8000. Vite forwards `/api/` requests to Django;
there are no frontend secrets or additional environment variables. Ports are fixed: stop a previous
server if the port is busy. A cold place lookup contacts live CTAN through the backend.

Checks and formatting:

```powershell
npm --prefix frontend run typecheck
npm --prefix frontend run lint
npm --prefix frontend run format:check
npm --prefix frontend run format
npm --prefix frontend run build
npm --prefix frontend run preview
```

ESLint covers JavaScript/TypeScript and React hook rules; Prettier covers frontend source and
configuration, with the official `prettier-plugin-tailwindcss` sorting Tailwind class lists using
the theme in `frontend/src/styles/app.css`. Run `npm --prefix frontend run format` after changing
utility classes; the check-only hook verifies the resulting order. Tailwind CSS utility classes are
the primary component styling mechanism. Keep
`frontend/src/styles/app.css` for the font, global base/accessibility rules, design tokens, and small
custom CSS that does not benefit from a utility class. The build also runs the TypeScript check.
TypeScript stays on 6.0 while the selected
typescript-eslint version supports versions below 6.1. No frontend automated test runner is configured;
interaction tests are deferred as described in `docs/features.md`. Use the checks above and manual
browser verification for current frontend changes.

The frontend follows the browser's `prefers-color-scheme` value on first visit. The theme button in the header toggles
between light and dark and saves an explicit choice under the `gadiruta.theme` local-storage key. Clear that key (or use
a private browser context) to verify system-preference behavior again. Check both themes when reviewing color, focus,
popover, and form-control changes.

Manrope is bundled through `@fontsource-variable/manrope`, with Segoe UI and then the generic
sans-serif font as fallbacks. The Latin variable font covers English/Spanish text and the UI's
font weights. Its OFL license is included in `frontend/public/fonts/Manrope-OFL.txt` and build output.

Build output goes to ignored `frontend/dist/`. Preview serves it at http://127.0.0.1:4173 and uses
the same local Django proxy; it is not a production deployment server.

### Manual place-selection check

1. Type `cadiz` into the starting-point field; select Cádiz using Down then Enter.
2. Type `puerto` into the destination field and choose a suggestion with the pointer.
3. Swap the places, edit a selected label, and clear a field. Editing must remove its confirmed identity.
4. Search for an unmatched name and check the empty state; an unavailable backend should show a retry.
5. Switch EN/ES, reload to check the saved preference, and try a narrow mobile viewport.

Only place selection is available: there is no timetable request, date/time control, or journey result yet.

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

The fixture README and `metadata.json` record provenance. CTAN tests use `httpx.MockTransport` and the
default test fixture rejects live HTTPX transport calls. Cache tests isolate the place-catalogue
key; they do not require PostgreSQL or an external cache service.

Provider-neutral catalogue/API tests use a structural `PlaceProvider` stub instead of CTAN
fixtures. Replace the service's provider factory in these tests; do not patch HTTP clients into
the service layer. Concrete implementation selection belongs in `transport/providers/wiring.py`.
Keep CTAN parsing and error-translation tests alongside the integration tests.

When adding a fixture:

1. Capture a representative real response during discovery.
2. Remove any data that should not be committed.
3. Name the fixture by behavior/use case.
4. Document unusual provider behavior in `docs/ctan-api.md`.
5. Add tests for the corresponding normalization behavior.

Live CTAN integration tests, if added, should be clearly separated from the default deterministic test suite.

---

## API documentation

Gadiruta's own API reference uses Scalar to display Django Ninja's generated OpenAPI schema.

Maintain transport-data attribution and the independence disclaimer in the top-level
`NinjaAPI(description=...)` in `gadiruta/api.py`, not in individual endpoint descriptions.

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

The `scalar-ninja` integration serves the reference page at the same URL as before. Its browser
bundle is pinned to a versioned jsDelivr URL in `gadiruta/api.py`; the browser needs internet access
to load that bundle and Scalar's default fonts. The HTML page and OpenAPI JSON are served by Django
without requiring debug mode or a frontend build. API requests from Scalar go directly to Gadiruta;
no Scalar proxy is configured, and Scalar's optional AI agent is disabled.

---

## Localization workflow

Frontend UI supports:

- English.
- Spanish.

Translation files:

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

### Git hooks

Install the shared checks once per clone, after installing the backend and frontend dependencies:

```powershell
uv sync --locked
npm --prefix frontend ci
uv run --locked pre-commit install --install-hooks
uv run --locked pre-commit run --all-files
uv run --locked pre-commit run --hook-stage pre-push --all-files
```

The versioned `.pre-commit-config.yaml` uses [pre-commit](https://pre-commit.com/) to install both
`pre-commit` and `pre-push` hooks. Repeat the install command in existing clones when hook types
change, and in every new clone: Git does not install hooks when cloning. Generated hook scripts
are local and are not committed. `uv` and `npm` must be on PATH.

Local hooks reuse tools from `uv.lock` and `frontend/package-lock.json`. Additional hooks come from
version-pinned [Gitleaks](https://github.com/gitleaks/gitleaks) and
[pre-commit-hooks](https://github.com/pre-commit/pre-commit-hooks) repositories. Initial installation
needs internet access to download their isolated environments and build Gitleaks; pre-commit uses
an available Go toolchain or downloads one when needed. No global Gitleaks installation is required.
Cached hook environments are reused on subsequent runs. Install/update project dependencies with
`uv sync --locked` and `npm --prefix frontend ci` before running checks.

#### Pre-commit: fast checks

- Gitleaks scans staged changes for likely credentials and private keys, with redacted output.
- Conflict-marker detection runs even outside a merge.
- JSON, YAML, and TOML files must parse successfully.
- Added or modified files must not exceed 1 MiB; review any legitimate exception and narrowly scope
  it in the hook configuration rather than disabling the guard.
- Filename checks reject case conflicts that break case-insensitive filesystems.

Normal commits run Python lint/format checks when Python files or Python tool configuration change,
and frontend lint/format checks when anything under `frontend/` changes. Hook configuration and
line-ending policy changes trigger both groups. Each triggered group checks its whole source tree
so configuration changes are covered too. Documentation-only commits skip lint/format checks but
still receive the applicable secret, conflict, file-size, and filename checks.

Gitleaks checks the staged diff even when invoked with `pre-commit run --all-files`; that command
is not a full repository/history secret audit. Deliberate example/test values must not justify
broad exclusions: if a false positive appears, review it and allow only the specific safe value or
finding. If a real credential is exposed, revoke/rotate it; deleting it from the latest file is
not sufficient.

Formatting is check-only: a failure blocks the commit without rewriting or staging source. Fix the
reported issues, review the diff, stage the corrected files, and retry the commit:

```powershell
uv run --locked ruff format .
npm --prefix frontend run format
```

Pre-commit temporarily stashes unstaged tracked changes while checking a normal commit and restores
them afterwards. Whole-tree checks can still see untracked source files. `.gitattributes` keeps
text checkouts on LF endings across Windows and Unix, matching the formatters.

#### Pre-push: correctness checks

Pushes run the full backend pytest suite, mypy, Django's system checks with
`.env.example`, and the frontend production build. These checks run even for documentation-only
changes. The build includes TypeScript checking and writes only ignored `frontend/dist/` output;
no frontend automated tests are configured or required while they remain deferred.

Current tests and system checks need neither PostgreSQL nor live CTAN access. The hook does not
load a private `.env`, apply migrations, start servers, or perform dependency security audits.
When database-backed tests or transport models are introduced, revisit the prerequisites and add a
missing-migrations check without applying migrations automatically.

Run the pre-push command above before pushing to diagnose failures locally. These hooks check the
current checkout, not an isolated copy of each pushed commit; use a clean checkout of the branch
being pushed. Local hooks can also be skipped, so they are not an enforcement boundary. Run the
same applicable checks in CI against the exact commits under review when CI is introduced; CI is
not configured yet. See the [pre-commit CI guidance](https://pre-commit.com/#usage-in-continuous-integration).

PyCharm's Git commits and pushes use the same installed hooks. Ensure PyCharm can find `uv` and
`npm` (restart the IDE after PATH changes); selecting a Python interpreter alone does not make npm
available.

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
