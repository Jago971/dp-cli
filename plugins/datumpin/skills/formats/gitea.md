# Gitea shapes

What the plugin writes to Gitea. Parent: [SKILL.md](SKILL.md).

## Ticket

Title: a noun phrase or imperative of 60 characters or fewer, no prefix. A decision ticket starts `Decide: `.

```
## Summary
<two or three lines: what changes, for whom, and why>

## Acceptance
- [ ] <one observable behaviour, in plain words>

## Out of scope
- <item; omit the section when empty>

## Notes
Source: <doc path and heading, or old ticket>
Depends on: #N, Owner/Repo#N
```

## Board

Title `Board`. Description: `The <Repo> kanban. Columns are the ticket's state; the datumpin plugin moves tickets as work progresses.` Columns, in order: Triage (default), Backlog, In Progress, Review, Testing, DoD, Done.

## Milestone

- Title: `vX.Y.Z – <theme>`, the theme 35 characters or fewer.
- Description: one sentence stating what is true when the milestone closes. A second line `Depends on: <milestone or Owner/Repo>` only when it does.
- Due date: only when a human sets one.

```
v0.2.0 – Approved addressings
Curated, approved addressings in dp and rur, with live data corrected to match the seeds.
```

## Comment

Every agent comment is one of four kinds.

**Pointer**: closing, redirecting or recording an outcome. One line:

`<Event>, <YYYY-MM-DD>. <Verdict>: <one line>. → <#N | doc path>`

Verdicts: `Covered`, `Carried forward`, `Obsolete`, `Duplicate`, `Done`.

```
Backlog reset, 2026-10-20. Carried forward: datetime and timezone convention. → #78
Tested by hand, 2026-10-22. Done: laptop, containers end -dev. → #107
```

A Tested Pointer (Event `Tested by hand`) records a hand test when the ticket leaves `test`; `gate` waits for one on every other ticket in the milestone.

**Scope**: the result of refining a ticket. The ticket sections, then the open questions:

```
## Scope
<Summary, Acceptance, Out of scope, as in Ticket>

## Open questions
1. <question> → <recommended answer>
```

**Progress**: a ticket moved to an earlier column. One line:

`<Event>, <YYYY-MM-DD>. Landed: <what> (PR #N). Left: <what>. → <column>`

```
AHJ board review, 2026-10-21. Landed: frontend image (PR #164). Left: smoke-test wiring. → In Progress
```

**Question**: one decision needed from a human:

```
**Question** · <topic>
<the question>
→ <recommended answer>
```

## Pull request

Title: as a ticket title. Labels: one `TYPE`, `ORIGIN/AGENT`, one `STAGE`.

```
## Summary
<one or two lines: what and why>

## Changes
- `<path or area>`: <what changed>

## Review
Evidence: <test count, --check result, what was verified by hand>

| # | Finding | Sev | Disposition |
|---|---|---|---|
| S1 | <Standards finding> | low | Fixed (<sha>) |
| P1 | <Spec finding> | medium | Dismissed: <reason> |

## Refs
Refs #N · Owner/Repo#N
See #N

## Check before merging
- <what a human checks; omit the section when empty>
```

- `Refs` names the tickets the PR works on, for the reader; board-sync moves only the ticket in the branch name, and a `Refs` line never moves a column. `See` names related tickets, which keep their column. Omit `See` when there are none.
- A PR with no local ticket replaces the `Refs` line with `No ticket: <reason>`. `conformance` fails a PR with neither that line nor a local ticket named (on a `Refs` line or in the branch).
- A PR stacked on another ticket's branch (`gitea-workflows`) opens its Summary with `Stacked on #N`.
- `Review` holds the `change-review` run before the PR opened. Finding ids are `S` (Standards), `P` (Spec), `X` (Security). A disposition is `Fixed (<sha>)`, `Dismissed: <reason>`, `Escalated: <to whom>` or `Deferred: #N`, where `#N` is a Triage ticket opened for it. With no findings, one row says so per axis. A promotion PR records its findings in the worksheet's Rev and Sec columns instead (`change-ready`).
