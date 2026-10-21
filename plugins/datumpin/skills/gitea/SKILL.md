---
name: gitea
description: Gitea - tickets, labels, milestones, comments and PRs through the tea CLI. Use when reading or writing anything in Gitea.
---

# Gitea

Gitea is the single source for tickets, milestones and the board. Read and write it with `tea`, Gitea's CLI.

## Calling tea

- Pass `--repo <owner>/<repo>` and `--login` on every call. The slug is the last two path segments of `git remote get-url origin`, `.git` removed: `ssh://git@host:2222/Datumpin/BDS.git` → `Datumpin/BDS`.
- Write as the agent login, `gitea.agent_login` in the flow config (default `squire`). Read as it too.
- For JSON, add `--output json --fields <list>`. Every field comes back as a string; `labels` is space-separated.
- For anything `tea` lacks, use `tea api --login <login> <endpoint>`, with the endpoint written without a leading slash.
- For a multi-line body, write it to a file in the scratchpad and pass `--description-file <file>`.
- In any body or comment, `#N` links an issue or PR in the same repo. Link another repo's as `Owner/Repo#N`, e.g. `Datumpin/WIKI#46`.
- When Gitea is unreachable (connection refused, timeout), print one log line saying so and take the calling flow's fallback.

| Need | Command |
|---|---|
| Open issues | `tea issues ls --repo R --login L --state open --limit 100 --output json --fields index,title,labels,milestone,assignees,author,url` |
| One issue, with body | `tea api --login L repos/R/issues/N` |
| Its comments | `tea api --login L repos/R/issues/N/comments` |
| Open PRs | `tea pulls ls --repo R --login L --output json --fields index,title,head,base,labels,url` |
| Milestones | `tea milestones ls --repo R --login L --output json` |
| Create an issue | `tea issues create --repo R --login L --title T --description-file F --labels "A,B" --milestone M` |
| Move labels | `tea issues edit N --repo R --login L --add-labels "A" --remove-labels "B"` |
| Human's username | `tea api --login H user`, its `login` field (the username, which can differ from the tea login name). `H` is the human's tea login in `tea login ls` (any login but the agent's); ask when there is more than one. |
| Assign | `tea issues edit N --repo R --login L --add-assignees USER`, with `USER` the username |
| Comment | `tea comment N --repo R --login L --description "<text>"` |
| Create a milestone | `tea milestones create --repo R --login L --title T --description D` |
| Find the board | `tea api --login L "repos/R/projects?state=open"`, the one titled `Board` |
| Its columns | `tea api --login L repos/R/projects/P/columns` |
| Tickets in a column | `tea api --login L "repos/R/projects/P/columns/C/issues?limit=50&page=N"` |
| Put a ticket on the board | `tea api --login L repos/R/projects/P/columns/C/issues/ID -X POST` |
| Move a ticket | `tea api --login L repos/R/projects/P/issues/ID/move -X POST -F column_id=C` |

Board calls take the issue's global `id` (from `repos/R/issues/N`), not its number `N`.

Page through `issues ls` with `--page` until a page returns fewer than the limit.

## What the agent may write

- Create issues and milestones, comment, change labels, milestones and assignees, and place or move tickets on the board.
- Create a repo's board when it has none (in `align`).
- Edit an issue's title or body only when the agent login created it. Text a human wrote changes through a comment that proposes the edit.
- Closing an issue, or closing or deleting a project, is a human's action.
- Every write needs the user's OK inside the running flow, and prints one log line.
- Everything written takes its shape from `formats`: tickets, milestones, comments (pointer, scope or question) and PRs.
- An improvement to the plugin or the shared CI found while working in any repo becomes a ticket in `Datumpin/DEVKIT`, in Triage, with a pointer to where it was found. A fix small enough to make in the same change is made there instead.

## Labels

Labels are written `SCOPE/NAME`. An issue carries at most one label per exclusive scope. Archived labels (`BOARD/*`, `ISSUE/*`, `STATUS/SUPERSEDED`, `TYPE/DISCUSS`, `TYPE/MERGE`) stay on old issues; apply only the labels below.

Org-level, shared by every repo:

| Scope | Labels | Meaning |
|---|---|---|
| `STATUS` | `BLOCKED`, `NEEDS-INFO` | Why it cannot move. |
| `TYPE` | `FEATURE`, `BUG`, `CHORE`, `DOCUMENTATION`, `DoD` | One per issue. `DoD` marks a DoD ticket. |
| `PRIORITY` | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW` | |
| `STAGE` | `PROT`, `PREP` | Target tier. `PROT` work is exploratory and skips DoD. |
| `ORIGIN` | `INTERNAL`, `AGENT` | `INTERNAL`: a dev todo managers can filter out. `AGENT`: the agent created it. Not exclusive. |

Repo-level: `COMPONENT/<NAME>`, one per entry in the repo's `components` config (name → folder globs). A ticket carries the component of every folder it touches; docs-only work carries none. Not exclusive.

## The board

Each repo has one Gitea project titled `Board`. Its column is the single record of a ticket's state; no label repeats it.

| Column | Means |
|---|---|
| Triage | New or vague; not yet scoped. The default column. |
| Backlog | Scoped, ready to start |
| In Progress | Being built; a branch exists |
| Review | PR open |
| Testing | Merged to `prep`, being tried on Hammond |
| DoD | Feature DoD signed, ready for release |
| Done | Closed: shipped on `main` in a tagged release, or no longer needed |

An open ticket not on the board is unsorted. A ticket moves to Done when it is closed.

## Milestones

- A milestone is one customer release, titled `vX.Y.Z – <theme>` and described in the milestone shape (see `formats`). Older milestones keep their names.
- Milestones belong to one repo. The same title in several repos marks cross-repo work.
- A package monorepo (PACKAGES) has no release of its own: each package versions on its own. A ticket that serves a consumer's release sits in a milestone with that consumer's title; the monorepo's own work has no milestone.

Milestones and the board are separate: the milestone says which release a ticket ships in, the column says where it is now. Other projects in a repo are humans' own; the flows read and write only `Board`. The project API needs Gitea 28 or later.
