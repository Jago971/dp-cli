# Decision log format

Decisions go in the repo's decision log, the doc `documentation-cross-cutting` names for it (for example `docs/plan/MIGRATION_LOG.md` in BDS). If the repo has none, create `docs/plan/DECISIONS.md` when the first decision is needed.

## Entry template

```md
### {Short title of the decision} ({YYYY-MM-DD})

{1-3 sentences: what's the context, what did we decide, and why.}
```

An entry can be a single paragraph. The value is in recording *that* a decision was made and *why*, not in filling out sections. Newest at the bottom.

## Optional lines

Only when they add genuine value. Most entries need none.

- **Status:** `proposed | accepted | superseded by <entry title>`. Useful when decisions are revisited.
- **Considered:** only when the rejected alternatives are worth remembering.
- **Consequences:** only when non-obvious downstream effects need to be called out.

## When to record

All three of these must be true:

1. **Hard to reverse**: the cost of changing your mind later is meaningful.
2. **Surprising without context**: a future reader will look at the code and wonder "why on earth did they do it this way?"
3. **The result of a real trade-off**: there were genuine alternatives and you picked one for specific reasons.

If a decision is easy to reverse, skip it: you'll just reverse it. If it's not surprising, nobody will wonder why. If there was no real alternative, there's nothing to record beyond "we did the obvious thing."

### What qualifies

- **Architectural shape.** "We're using a monorepo." "The write model is event-sourced, the read model is projected into Postgres."
- **Integration patterns between contexts.** "Ordering and Billing communicate via domain events, not synchronous HTTP."
- **Technology choices that carry lock-in.** Database, message bus, auth provider, deployment target. Not every library: just the ones that would take a quarter to swap out.
- **Boundary and scope decisions.** "Customer data is owned by the Customer context; other contexts reference it by ID only." The explicit no-s are as valuable as the yes-s.
- **Deliberate deviations from the obvious path.** "We're using manual SQL instead of an ORM because X." Anything where a reasonable reader would assume the opposite.
- **Constraints not visible in the code.** "We can't use AWS because of compliance requirements."
- **Rejected alternatives when the rejection is non-obvious.** If you considered GraphQL and picked REST for subtle reasons, record it; otherwise someone will suggest GraphQL again in six months.
