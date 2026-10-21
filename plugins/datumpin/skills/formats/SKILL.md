---
name: formats
description: Formats - the fixed shape of everything the plugin prints or writes - terminal lines, prompts, board, drafts, questions, handover, tickets, milestones, comments, PRs, commits, branches. Use before printing a workflow message or writing to Gitea or git.
---

# Formats

Everything a flow prints or writes has a shape, so the plugin reads like a CLI tool with code behind it. Use the shape exactly: no preamble, no recap, no sign-off. Conversation outside a shape (a `shape` interview, an answer to a direct question) stays to three lines or fewer.

A flow that prints or writes something new adds its shape to this file before it writes anything.

| Output | Shape |
|---|---|
| Any event or result in the terminal | Log line |
| A yes/no or choice for the user | Prompt |
| The kanban | Board view |
| Parked work at session start | Status line |
| Drift between code, tickets and plans | Drift report |
| Tickets or milestones before pushing | Draft list |
| Superseded tickets left for a human to close | To-close list |
| The end of a session, for the next one | Handover |
| A scoping question | Shaping question |
| The next choice in a flow | Guide prompt |
| Gitea issue | Ticket |
| Gitea milestone | Milestone |
| Gitea comment | Comment (pointer, scope, progress, question) |
| Gitea pull request | Pull request |
| Git commit / branch | Commit, Branch |
| Gitea project | Board (one per repo, see `gitea`) |

## Quiet steps

While a flow step runs, nothing is printed between tool calls: no "checking…", no plan, no running commentary. The step ends with its output in its shape (log lines, a board, a draft list) and, when a choice follows, one Prompt per question. Reasons and detail wait until the user asks for them. A finding that changes what the user decides goes in the output as a log line, never as prose between calls.
The three-line cap above applies only outside a flow step.

## Terminal

### Log line

`[<flow> <ref>] <event> · <detail> · <detail>`

- `<flow>` is the flow name; `<ref>` is `#N`, `Owner/Repo#N` or a milestone, omitted when there is none.
- One line per event; a run ends with one summary line.
- Outcome words are upper case: `DONE`, `FAILED`, `SKIPPED`, `PASS`, `CHANGES`, `READY`, `BLOCKED`.
- A failure says what failed and the next step: `FAILED · <what> · <next step>`.

```
[board] synced Datumpin/BDS · 61 open · 1 PR
[shape #31] created · Backlog · TYPE/FEATURE · COMPONENT/API · v0.4.0
[shape] FAILED · Gitea unreachable · 2 drafts saved to .factory/outbox/
[shape] DONE · 3 created · 0 failed
```

### Status line

Printed by the plugin's session-start hook, one line, ASCII only:

`datumpin status | <Owner/Repo>: Triage <n>, open PRs <n> | Datumpin/DEVKIT: Triage <n>. If Triage is not empty, offer the user a short sort (/datumpin:board).`

`-` stands for a repo with no Board. When a count is above zero, mention it once in the first reply; do not repeat it.

### Prompt

`? <question> (<option> / <option>)`

```
? Push all 3 tickets? (yes / edit N / drop N)
? Move #44 to In Progress and assign MattM? (yes / no)
```

### Board view

```
Datumpin/BDS · synced 2026-10-20 10:42 · 14 open · 1 PR
TRIAGE (2)        #27 BDS Tagging System
                  #26 Sampling
BACKLOG (1)       #25 Addressing Validation · FEATURE · HIGH · API · v0.4.0
IN-PROGRESS (0)
REVIEW (0)
TESTING (0)
DOD (0)
UNSORTED (11)     #24 #23 #22 #21 #20 #19 #18 #17 #16 #15 #14
Milestones        v0.4.0 – Sampling · 2 of 9 done · 1 in DoD
PRs               #29 Pilot the datumpin plugin · chore/datumpin-plugin → prep
Flags             #25 no milestone · #26 STATUS/BLOCKED · #14 to close
Next              1. #25 Addressing Validation · HIGH, unblocked, in v0.4.0
```

- The sync time is date and time. Every column prints, empty ones as a single line.
- A column with more than 8 tickets lists numbers only.
- `Milestones` lists each open milestone, earliest first: closed tickets of its total, and how many sit in DoD.
- `Milestones`, `PRs`, `Flags` and `Next` come last, in that order; an empty one is omitted.

### Drift report

```
Drift · Datumpin/BDS · 2026-10-20 · mode Reset · full report .factory/align-2026-10-20.md
DONE-OPEN (13)     #1 covered by POST /extract/addressing → close
                   #10 route review in MIGRATION_LOG → close
OFF-COURSE (2)     #27 tag tables dropped (MIGRATION_LOG) → close
NO-TICKET (40)     FORWARD_PLAN 4.1 headstart addressings → new ticket
NO-DIRECTION (1)   #15 realtime scoping → keep in Triage
DOCS-BEHIND (10)   ROADMAP says .gitea/workflows not created → doc fix
? Draft the changes? (yes / show KIND / skip KIND)
```

- Every kind prints, empty ones as a single line; a kind with more than 5 findings shows the first 3 and `+N more`.
- Each finding is `<ticket or source> <one-line reason> → <action>`.

### Draft list

```
Drafts · 3 tickets · milestone v0.4.0 – Sampling
1. Add sampling rate to processor config · FEATURE · HIGH · PREP
   acceptance 3 · out of scope 1
2. ...
? Push all? (yes / edit N / drop N)
```

A draft milestone prints first as `M · <title> · <goal sentence>`.

### To-close list

The tickets a flow superseded but left open, since closing is a human's action. Each line carries its pointer verdict:

```
To close · 2 superseded
- #96 · Carried forward → #120
- #97 · Duplicate → #88
```

### Handover

```
Handover · <repo>\.factory\handoff-2026-10-21.md
Next prompt   Read <repo>\.factory\handoff-2026-10-21.md, then run /datumpin:board and continue #89.
Your steps    1. Merge DEVKIT#99
              2. Merge Datumpin/AHJ#169
```

- `Next prompt` is one line the user pastes as is; it names the document and the next flow step.
- `Your steps` lists only what the human must do first, numbered; `none` when empty.

### Guide prompt

```
Guide · ticket flow · #52 · review (dev)
Done          change-review · CHANGES · Standards 2 · Spec 1
1. fix        Apply the dispositions, then commit
2. pr         Push and open the PR, with its Review section
3. stop
? Next? (1 / 2 / 3)
```

- The first line is the position: flow, ticket when there is one, step and its environment.
- `Done` is the last step's outcome line, omitted before the first step.
- Each choice is the step's name and its `does` line from the flow map; a fork into another flow ends `→ <flow> flow`. `stop` is always last.

### Shaping question

```
Q3 · <topic>
<the question, one or two lines>
→ <recommended answer>
```

One question per turn. "yes" accepts the recommendation.

## Gitea

### Ticket

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

### Board

Title `Board`. Description: `The <Repo> kanban. Columns are the ticket's state; the datumpin plugin moves tickets as work progresses.` Columns, in order: Triage (default), Backlog, In Progress, Review, Testing, DoD, Done.

### Milestone

- Title: `vX.Y.Z – <theme>`, the theme 35 characters or fewer.
- Description: one sentence stating what is true when the milestone closes. A second line `Depends on: <milestone or Owner/Repo>` only when it does.
- Due date: only when a human sets one.

```
v0.2.0 – Approved addressings
Curated, approved addressings in dp and rur, with live data corrected to match the seeds.
```

### Comment

Every agent comment is one of four kinds.

**Pointer**: closing, redirecting or recording an outcome. One line:

`<Event>, <YYYY-MM-DD>. <Verdict>: <one line>. → <#N | doc path>`

Verdicts: `Covered`, `Carried forward`, `Obsolete`, `Duplicate`, `Done`.

```
Backlog reset, 2026-10-20. Carried forward: datetime and timezone convention. → #78
```

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

### Pull request

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

- `Refs` names only the tickets the PR works on; board-sync moves them with the PR. `See` names related tickets, which keep their column. Omit `See` when there are none.
- A PR with no local ticket replaces the `Refs` line with `No ticket: <reason>`. `conformance` fails a PR with neither that line nor a local ticket board-sync moves (on a `Refs` line or in the branch).
- A PR stacked on another ticket's branch (`gitea-workflows`) opens its Summary with `Stacked on #N`.
- `Review` holds the `change-review` run before the PR opened. Finding ids are `S` (Standards), `P` (Spec), `X` (Security). A disposition is `Fixed (<sha>)`, `Dismissed: <reason>`, `Escalated: <to whom>` or `Deferred: #N`, where `#N` is a Triage ticket opened for it. With no findings, one row says so per axis. A promotion PR records its findings in the worksheet's Rev and Sec columns instead (`definition-of-done`).

## Git

### Commit

`<area>: <what changed>`

- `<area>` is the folder, service or topic in lower case (`docs`, `api`, `processor`, `ci`, `gitignore`); the subject is 72 characters or fewer.
- An optional body gives the why in short lines, and `Refs #N` when there is a ticket (`See #N` for one it only relates to).
- No AI attribution trailer.

### Branch

`<type>/<issue>-<slug>`, e.g. `feat/44-headstart-ap-blac-chpg`. `<type>` is `feat`, `fix`, `chore` or `docs`. Without a ticket: `<type>/<slug>`.
