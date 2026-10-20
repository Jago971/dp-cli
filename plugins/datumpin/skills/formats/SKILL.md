---
name: formats
description: Formats - the fixed shape of everything the plugin prints or writes - terminal lines, prompts, board, drafts, questions, tickets, milestones, comments, PRs, commits, branches. Use before printing a workflow message or writing to Gitea or git.
---

# Formats

Everything a flow prints or writes has a shape, so the plugin reads like a CLI tool with code behind it. Use the shape exactly: no preamble, no recap, no sign-off. Conversation outside a shape (a `shape` interview, an answer to a direct question) stays to three lines or fewer.

A flow that prints or writes something new adds its shape to this file before it writes anything.

| Output | Shape |
|---|---|
| Any event or result in the terminal | Log line |
| A yes/no or choice for the user | Prompt |
| The kanban | Board view |
| Drift between code, tickets and plans | Drift report |
| Tickets or milestones before pushing | Draft list |
| A scoping question | Shaping question |
| Gitea issue | Ticket |
| Gitea milestone | Milestone |
| Gitea comment | Comment (pointer, scope, question) |
| Gitea pull request | Pull request |
| Git commit / branch | Commit, Branch |
| Gitea project | Board (one per repo, see `gitea`) |

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
PRs               #29 Pilot the datumpin plugin · chore/datumpin-plugin → prep
Flags             #25 no milestone · #26 STATUS/BLOCKED
Next              1. #25 Addressing Validation · HIGH, unblocked, in v0.4.0
```

- The sync time is date and time. Every column prints, empty ones as a single line.
- A column with more than 8 tickets lists numbers only.
- `PRs`, `Flags` and `Next` come last, in that order; an empty one is omitted.

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

Every agent comment is one of three kinds.

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

## Refs
Refs #N · Owner/Repo#N

## Check before merging
- <what a human checks; omit the section when empty>
```

## Git

### Commit

`<area>: <what changed>`

- `<area>` is the folder, service or topic in lower case (`docs`, `api`, `processor`, `ci`, `gitignore`); the subject is 72 characters or fewer.
- An optional body gives the why in short lines, and `Refs #N` when there is a ticket.
- No AI attribution trailer.

### Branch

`<type>/<issue>-<slug>`, e.g. `feat/44-headstart-ap-blac-chpg`. `<type>` is `feat`, `fix`, `chore` or `docs`. Without a ticket: `<type>/<slug>`.
