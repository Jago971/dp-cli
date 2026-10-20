---
name: board
description: Board - sync this repo's Gitea tickets, show the kanban, suggest what to work on next. Use at the start of a session, or when asked for the board, the backlog, or what to do next.
model: sonnet
effort: low
---

# Board

Gitea holds the board, the repo's project titled `Board`; this flow reads it, shows it and proposes the next ticket. Use the `gitea` skill for every call and the `formats` skill for everything printed or written.

## Steps

1. **Config.** Read the plugin defaults at `../../defaults/flow.yaml` (relative to this skill's base directory), then the repo's `.claude/flow.yaml` if present; repo keys win.
2. **Repo.** Resolve the slug from `git remote get-url origin`.
3. **Outbox.** If `.factory/outbox/` holds drafts from an offline `shape`, list them and push the ones the user accepts, exactly as `shape` step 6 does.
4. **Sync.** Fetch the board's columns and the tickets in each, every open issue, and every open PR. If Gitea is unreachable, print `.factory/board.md` with its sync time marked stale, and stop. If the repo has no board, say so and point to `align`.
5. **Sort.** Each ticket sits in its board column. An open issue not on the board goes in `UNSORTED`.
6. **Flag.** Collect: no `TYPE`; no milestone (Backlog onwards); any `STATUS/*`; a closed ticket outside Done; an open ticket in Done; no `COMPONENT` where the repo declares components.
7. **Suggest.** Pick `board.suggest` tickets from Backlog, skipping any with a `STATUS` label. Order by priority (`CRITICAL` first, none last), then the earliest open milestone, then the oldest. Give one reason each. With Backlog empty, suggest from Triage and say each needs shaping.
8. **Show.** Print the board view, then write it to `.factory/board.md` with the sync time. If `.factory/` is not gitignored, add it to `Flags`.
9. **Triage offer.** When `UNSORTED` or `Flags` is non-empty, offer to triage: propose a column, `TYPE`, `PRIORITY` and `COMPONENT` labels per ticket in one compact list, and apply the lines the user accepts.
10. **Pick.** When the user picks a ticket: a Triage ticket goes to `shape #N`; a Backlog ticket moves to In Progress and is assigned to the user's Gitea account, after their OK.

## Done when

- The board printed came from this sync, or is the cache clearly marked stale.
- Suggestions and flags are printed, each with its reason.
- Every write was accepted by the user and printed as a log line.
