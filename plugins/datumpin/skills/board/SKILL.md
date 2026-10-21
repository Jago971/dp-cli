---
name: board
description: Board - sync this repo's Gitea tickets, show the kanban, suggest what to work on next. Use at the start of a session, or when asked for the board, the backlog, or what to do next.
model: sonnet
effort: low
---

# Board

Gitea holds the board, the repo's project titled `Board`; this flow reads it, shows it and proposes the next ticket. Use the `gitea` skill for every call and the `formats` skill for everything printed or written, including its Quiet steps rule.

## Steps

1. **Config.** Read the plugin defaults at `../../defaults/flow.yaml` (relative to this skill's base directory), then the repo's `.claude/flow.yaml` if present; repo keys win.
2. **Repo.** Resolve the slug from `git remote get-url origin`.
3. **Outbox.** If `.factory/outbox/` holds drafts from an offline `shape`, list them and push the ones the user accepts, exactly as `shape` step 6 does.
4. **Sync.** Fetch the board's columns and the tickets in each (every page), every open issue, the last comment of each open issue that has comments (`gitea`, Last comment), every open PR, and the open milestones with their closed and open counts. If Gitea is unreachable, print `.factory/board.md` with its sync time marked stale, and stop. If the repo has no board, say so and point to `align`.
5. **Sort.** Each ticket sits in its board column. An open issue not on the board goes in `UNSORTED`.
6. **Flag.** Collect: no `TYPE`; no milestone (Backlog onwards); any `STATUS/*`; a closed ticket outside Done; an open ticket in Done; an open ticket whose last agent comment is a `Covered`, `Carried forward`, `Obsolete` or `Duplicate` pointer (to close); no `COMPONENT` where the repo declares components.
7. **Suggest.** Pick `board.suggest` tickets from Backlog, skipping any with a `STATUS` label. Order them, since a release ships one milestone at a time:
   1. a `CRITICAL` ticket, wherever it sits;
   2. the earliest open milestone's tickets, then the next milestone's, then tickets with none;
   3. within each, by priority (none last), then the oldest.

   Give one reason each. With Backlog empty, suggest from Triage and say each needs shaping.
8. **Show.** Print the board view, including its `Milestones` line: per open milestone, closed tickets of its total (Gitea's counts) and how many sit in the DoD column (from the board), then write it to `.factory/board.md` with the sync time. If `.factory/` is not gitignored, add it to `Flags`.
9. **Triage offer.** When `UNSORTED` or `Flags` is non-empty, offer to triage: propose a column, `TYPE`, `PRIORITY` and `COMPONENT` labels per ticket in one compact list, and apply the lines the user accepts.
10. **Pick.** When the user picks a ticket: a Triage ticket goes to `shape #N`; a Backlog ticket moves to In Progress and is assigned to the user's Gitea username (the `gitea` skill's Human's username, then Assign), after their OK.

## Done when

- The board printed came from this sync, or is the cache clearly marked stale.
- Suggestions and flags are printed, each with its reason.
- Every write was accepted by the user and printed as a log line.
