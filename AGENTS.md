# Gadiruta Agent Instructions

## Purpose

These instructions govern how coding agents should work on Gadiruta.

Gadiruta is a Cádiz-focused public transport web application. The durable product definition lives in `docs/product.md`.
Current implemented capabilities are tracked in `docs/features.md`.

Before making changes, read the relevant project documentation and inspect the current repository state.

## Working method

Work iteratively.

Use this cycle:

```text
inspect
  ↓
plan a small coherent change
  ↓
implement
  ↓
test
  ↓
review diff
  ↓
update relevant documentation
  ↓
commit
  ↓
continue
```

Do not attempt to implement the entire product specification in one large pass.

Before starting a change:

1. Inspect the current repository.
2. Run `git status`.
3. Read the relevant code and documentation.
4. Identify the smallest coherent next milestone.
5. Confirm upstream CTAN behavior when the implementation depends on uncertain API assumptions.

After implementing a change:

1. Run the relevant tests, linting, and type checks.
2. Inspect the resulting `git diff`.
3. Fix obvious issues.
4. Update affected documentation.
5. Create a scoped Git commit.
6. Continue only after the repository is in a sensible state.

Prefer working vertical slices over building large disconnected backend/frontend subsystems.

## Git discipline

Use Git as part of the development workflow.

Commits should be:

- Focused on one coherent concern.
- Small enough to review.
- Large enough to represent a meaningful repository state.
- Written with clear English commit messages.

Examples:

```text
chore: initialize Django backend
chore: initialize React frontend
feat: add CTAN API client
test: add CTAN line response fixtures
feat: expose places search endpoint
feat: connect place autocomplete to API
feat: add Spanish translations for journey search
fix: handle CTAN timeout responses
```

Avoid vague commits such as:

```text
updates
frontend stuff
more fixes
complete app
```

Do not:

- Commit secrets, `.env`, local databases, virtual environments, `node_modules`, build artifacts, editor junk, or cache
  files.
- Rewrite history unnecessarily.
- Use destructive Git operations without explicit instruction.
- Modify unrelated code as part of a feature.
- Bundle unrelated refactors into a feature commit.

If a significant refactor is required, prefer a separate refactor commit.

## Sources of truth

Use the following documents for different purposes:

- `docs/product.md`: durable product goals, scope, principles, and future direction.
- `docs/features.md`: current functional capabilities and implementation status.
- `docs/architecture.md`: major architecture and system boundaries.
- `docs/ctan-api.md`: discoveries and quirks of the upstream CTAN API.
- `docs/decisions.md`: significant architectural/product decisions and why they were made.
- `docs/development.md`: local setup, commands, tooling, and development conventions.
- Django Ninja/OpenAPI: canonical endpoint-level reference for Gadiruta's own API.
- Git history: what changed and when.

Do not duplicate the same information across documents unnecessarily.

## Documentation maintenance

Update documentation in the same commit as the implementation whenever practical.

Use this mapping:

```text
Feature behavior         → docs/features.md
Architecture             → docs/architecture.md
CTAN discoveries         → docs/ctan-api.md
Major decisions          → docs/decisions.md
Developer workflow       → docs/development.md
Product scope            → docs/product.md
Own API contract         → code/OpenAPI schemas and descriptions
```

Do not maintain a verbose agent-session or daily development diary.

## Product constraints

The MVP is Cádiz-focused and centers on:

- Direct public transport journey search.
- Schedules.
- Lines.
- Stops / population centres.
- Relevant service notices.

Do not expand MVP scope into:

- Multi-leg transfer routing.
- Arbitrary street-address routing.
- Walking directions.
- Driving.
- Flights.
- Accounts/authentication.
- Payments.
- Native mobile apps.
- Push notifications.
- Complex maps.
- Full Andalusia coverage.
- Custom routing algorithms.

Unless `docs/product.md` has been explicitly changed, these remain out of scope.

## Backend conventions

Backend stack:

- Python
- Django 6.1.1
- Django Ninja
- PostgreSQL
- httpx
- pytest
- pytest-django

The frontend must call Gadiruta's Django API, not CTAN directly.

Keep the CTAN integration behind a dedicated adapter/client boundary.

Do not leak raw CTAN response formats into the frontend-facing API.

Use typed Django Ninja schemas and generated OpenAPI documentation as the canonical API reference.

Normal automated tests must not depend on the live CTAN API. Prefer representative saved fixtures.

## Frontend conventions

Frontend stack:

- React 19
- TypeScript
- Vite
- React Router
- TanStack Query
- react-i18next

Keep dependencies relatively small.

Prefer bespoke CSS and a small design system over a heavy generic UI library.

The visual direction is inspired by `https://clicks.coffee/`:

- Spacious.
- Strong typography.
- Minimal visual noise.
- Clear hierarchy.
- Large comfortable controls.
- Mobile-first.
- Friendly rather than bureaucratic.

Do not copy the site literally.

## Language

Code, variable names, comments, documentation, API field names, and Git commits are written in English.

The UI must support:

- English.
- Spanish.

English is the source/fallback language.

All user-facing strings must go through the translation system. Do not scatter literal UI text through React components.

## CTAN discovery

Do not blindly implement assumptions about the upstream API.

Before deeply depending on an endpoint or data model:

1. Inspect the CTAN documentation.
2. Exercise representative real responses where appropriate.
3. Save representative fixtures.
4. Document important discoveries in `docs/ctan-api.md`.
5. Normalize upstream data behind Gadiruta's own domain/API model.

The application should tolerate missing fields, empty arrays, HTTP errors, timeouts, and inconsistent upstream records.
