---
name: fastapi-service-architecture
description: FastAPI services - routers/services/database layering, route naming, tests. Use when adding a router, model or settings field; DB and settings rules in siblings
---

# FastAPI service architecture

The default structure for every FastAPI service (AHJV2's backend, BDS's `api`/`processor`, curator), so a developer or Claude moving between them finds the same layout.

Branches that load a sibling file:

| When | File |
|---|---|
| Adding or changing a settings field, an env var, CORS | [SETTINGS.md](SETTINGS.md) |
| Running a service as more than one instance, or deciding what varies per instance | [MULTI-INSTANCE.md](MULTI-INSTANCE.md) |
| Writing a model or a list query | [DB-PATTERNS.md](DB-PATTERNS.md) |

Env files, seeding, ports, networks and compose generation belong to `config-led-deployment`. Migrations belong to `alembic-migrations`.

## Three layers: `routers/` → `services/` → `database/`

- **`routers/`**: one file per resource or workflow area. Routers translate HTTP into service calls: Pydantic request/response models, status codes, and the call into `services/`.
- **`services/`**: the business logic, framework-agnostic where possible so it is unit-testable without FastAPI. A resolver used by more than one router is its own module here (an `extraction_config.py` used by both a `config` and an `extraction` router).
- **`database/`**: SQLAlchemy models, Alembic migrations (`migrations/`, `alembic.ini`) and the seed loader. Routers reach the database through `services/`.

Each of the three folders has a `README.md` saying what it owns and what it leaves out (`routers/` adds a per-endpoint status table, see `api-documentation`).

## Name routes for the workflow

A router is named for what a caller is trying to do: `curation.py` (`/curation/pull`, `/curation/push`), not `addressing.py` mirroring an `Addressing` table. The workflow-named router is the contract that carries across a service's instances.

Before adding a router, check whether an existing one already serves the same purpose under another name, and consolidate.

## Tests

`unit` / `integration` / `contract` markers (see `testing-conventions`). `conftest.py` sets an in-memory SQLite database URL before anything imports `config` or `database.engine`, so test runs stay off the instances' real DB files.

## Done when

- `grep -rn "from database" routers/` finds nothing.
- `grep -rn "sqlalchemy.dialects.postgresql" .` finds nothing.
- Each of `routers/`, `services/`, `database/` has a README.
- The new route's name describes a workflow, and no existing router covers the same purpose.
