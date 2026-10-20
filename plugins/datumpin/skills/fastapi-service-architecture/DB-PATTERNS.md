# Database patterns

Parent: [SKILL.md](SKILL.md).

## UUID primary keys are strings

Services default to SQLite locally and may run Postgres in production. `sqlalchemy.dialects.postgresql.UUID` works only on Postgres. Use `String(36)` storing `str(uuid.uuid4())` with a Python default, which works on both, and compare against `str(...)` on the Python side.

## Eager-load relationships on list endpoints

SQLAlchemy loads relationships lazily, which suits a single-object lookup. A list endpoint that touches a relationship per row fires one extra query per row per relationship, so a list of 144 rows reading `s.customer.*` and `s.sourcebuild.*` made about 300 extra round trips. State the loading strategy in the query:

```python
sources = (
    db.query(Source)
    .join(Customer)
    .options(joinedload(Source.customer), joinedload(Source.sourcebuild))
    .order_by(Customer.customer_code, Source.source_code_1)
    .all()
)
```

- `joinedload` for many-to-one traversals, chained for multi-level (`joinedload(A.b).joinedload(B.c)`).
- `selectinload` for a one-to-many collection, where a joined load multiplies the result rows.

## Done when

- `grep -rn "sqlalchemy.dialects.postgresql" .` finds nothing.
- Each list endpoint that reads a relationship per row has an eager-load option for it, and a test asserting a query-count ceiling.
