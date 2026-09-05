# Development

This document describes how to work on Gadiruta locally.

Update commands and setup instructions whenever tooling changes.

---

## Repository

Expected layout:

```text
gadiruta/
    AGENTS.md
    README.md
    backend/
    frontend/
    docs/
```

---

## Prerequisites

Initial expected prerequisites:

- Git.
- Python version compatible with Django 6.1.1.
- PostgreSQL.
- Node.js suitable for React 19 / current Vite.
- npm, pnpm, or another explicitly selected package manager.

Record exact supported versions once the project is bootstrapped.

---

## Backend

Stack:

- Django 6.1.1.
- Django Ninja.
- PostgreSQL.
- httpx.
- pytest.
- pytest-django.

Document exact setup commands after backend initialization.

Expected topics:

```text
Create virtual environment
Install dependencies
Configure environment variables
Create PostgreSQL database
Run migrations
Start Django development server
Run backend tests
Run lint/format checks
```

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

Do not commit `.env` files or secrets.

Provide an example environment file when configuration is introduced, for example:

```text
.env.example
```

Document every required variable here.

Likely categories:

- Django secret/config.
- PostgreSQL connection.
- Allowed hosts / CORS configuration.
- CTAN integration configuration if required.

---

## Database

Use PostgreSQL.

Document:

- Local database creation.
- Connection configuration.
- Migration commands.
- Reset/reseed instructions if fixtures or sync data are introduced.

Do not commit local database files/dumps unless they are intentional test fixtures.

---

## CTAN fixtures

Normal automated tests must not depend on live CTAN availability.

Representative upstream responses should live under something similar to:

```text
backend/tests/fixtures/ctan/
```

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
- Add docstrings/descriptions where they improve generated docs.
- Do not manually duplicate the full endpoint contract under `docs/`.

Document the local OpenAPI/docs URL here after backend routing is initialized.

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
