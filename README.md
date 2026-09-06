# Gadiruta

Gadiruta is a Cádiz-focused public transport web application inspired conceptually by Rome2Rio.

The MVP focuses on making official CTAN transport data easier to use for:

- Direct journey search.
- Schedule lookup.
- Line exploration.
- Stop / population centre exploration.
- Relevant service notices.

## Stack

### Backend

- Python
- Django 6.1.1
- Django Ninja
- PostgreSQL
- httpx
- pytest / pytest-django

### Frontend

- React 19
- TypeScript
- Vite
- Tailwind CSS
- Lucide React
- React Router
- TanStack Query
- react-i18next

## Architecture

```text
Browser / React
       ↓
  Django API
       ↓
  CTAN adapter
       ↓
    CTAN API
```

The frontend never depends directly on the CTAN API.

## Documentation

- [`docs/product.md`](docs/product.md) — product goals, MVP scope, principles, and future direction.
- [`docs/features.md`](docs/features.md) — current feature inventory and implementation status.
- [`docs/architecture.md`](docs/architecture.md) — major architecture and system boundaries.
- [`docs/ctan-api.md`](docs/ctan-api.md) — upstream CTAN API discoveries and quirks.
- [`docs/decisions.md`](docs/decisions.md) — significant decisions and rationale.
- [`docs/development.md`](docs/development.md) — local development setup and commands.
- [`AGENTS.md`](AGENTS.md) — instructions for coding agents working on the repository.

Gadiruta's own API reference is generated from Django Ninja/OpenAPI and should not be manually duplicated in
documentation.

## Development approach

Development is iterative and Git-driven. Work should be delivered in small, coherent, tested commits rather than one
large implementation pass.

See `AGENTS.md` for the complete agent workflow.
