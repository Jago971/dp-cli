---
name: api-documentation
description: Documenting HTTP APIs - endpoint docstrings, router READMEs, docs/reference/api. Use when adding or editing a FastAPI route.
---

# API documentation

## Endpoint docstrings

Router handlers use the docstring shape from `code-comments-and-docstrings`, and populate `summary=`, `description=` and `response_model` from it, so the generated `/docs` page carries the information. The framework's defaults leave Swagger UI thin.

## `docs/reference/api/`

An API with more than a handful of endpoints gets this folder (governed by `documentation-cross-cutting`), covering:

- The authentication and authorization model.
- The cross-cutting error response shape (a 4xx/5xx body).
- A link to each router README. The router README's status table is the only route list.

## Per-router status table

Each router folder's README has a table of endpoint, status (built/planned/deprecated) and one line of design rationale. Where two routers look alike, it states why they are separate (a genuine second purpose, or a duplicate to consolidate).

Update the table in the same change as the route.

## Done when

- Every route handler sets `summary` and `description` (check `/docs`).
- The router README table lists every route in the router file, each with a status.
- `docs/reference/api/` covers auth and the error shape, and links every router README.
