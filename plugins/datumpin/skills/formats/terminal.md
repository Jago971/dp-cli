# Terminal shapes

The terminal shapes beyond Log line and Prompt. Parent: [SKILL.md](SKILL.md).

## Status line

Printed by the plugin's session-start hook, one line, ASCII only:

`datumpin status | <Owner/Repo>: Triage <n>, open PRs <n> | Datumpin/DEVKIT: Triage <n>. If Triage is not empty, offer the user a short sort (/datumpin:board).`

`-` stands for a repo with no Board. When a count is above zero, mention it once in the first reply; do not repeat it.

## Board view

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

## Drift report

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

## Draft list

```
Drafts · 3 tickets · milestone v0.4.0 – Sampling
1. Add sampling rate to processor config · FEATURE · HIGH · PREP
   acceptance 3 · out of scope 1
2. ...
? Push all? (yes / edit N / drop N)
```

A draft milestone prints first as `M · <title> · <goal sentence>`.

## To-close list

The tickets a flow superseded but left open, since closing is a human's action. Each line carries its pointer verdict:

```
To close · 2 superseded
- #96 · Carried forward → #120
- #97 · Duplicate → #88
```

## Handover

```
Handover · .factory/handoff-2026-10-21.md
Next prompt   In dp-cli run `dp guide`: it offers #89 at its step. Then paste: Read .factory/handoff-2026-10-21.md.
Your steps    1. Merge DEVKIT#99
              2. Merge Datumpin/AHJ#169
```

- `Next prompt` is one line that tells the user to run `dp guide` in dp-cli with the recommended ticket and step, and names the document by its repo-relative path.
- `Your steps` lists only what the human must do first, numbered; `none` when empty.

## Step ending

```
Result    <one line: done, or what is open>
You       1. <the action>, <its effect>   (recommended)
          2. <the alternative>, <its effect>
          3. Other, say what
Session   stay to answer · /exit when done, then dp guide offers <step>
```

- Every agent step ends with this block, never an open question: one required input, as numbered choices, the recommended one first, `Other` for anything else.
- Each choice says its effect. `Session` says whether to stay or `/exit`, and what `dp guide` then offers.

## Guide prompt

```
Guide · ticket flow · #52 · review (dev)
Done          change-review · CHANGES · Standards 2 · Spec 1
1. fix        Apply the dispositions, then commit
2. pr         Push and open the PR, with its Review section
   ───────────
3. flows…     Start or switch to any flow
4. stop
? Next? (1 / 2 / 3 / 4)
```

- The first line is the position: flow, ticket when there is one, step and its environment.
- `Done` is the last step's outcome line, omitted before the first step.
- Each choice is the step's name and its `does` line from the flow map; a human step's line names the person (`You merge…`). This flow's steps come first; below a `───` line come the forks whose check holds (one into another flow ends `→ <flow> flow`), then `flows…`, and `pause` in a ticket. With no ticket current the choices are the home menu: `tickets`, `resume…` when one is paused, `end`, `flows…`. `stop` is always last.
- With no position, the first line is `Guide · start` and the choices are the home menu.
- `dp guide` at a terminal prints the first line and shows the choices as an arrow-key menu.

## Job prompt

`dp guide` starts Claude Code with it for an agent step; without `claude` on the PATH, the person pastes it into a session on the model the panel names.

```
Step build of #125: read .factory/jobs/125/build.md and do it.
Step gate of the release flow: read .factory/jobs/release/gate.md and do it.
```

- The brief path is `.factory/jobs/<ticket, or flow>/<step>.md`. `dp tokens` books the turns after the prompt to that step, so keep the path in the prompt.
- A review brief asks for `findings.json` beside it; `dp guide` asks the person for each disposition (Pull request, Review) and later briefs list them.

## Shaping question

```
Q3 · <topic>
<the question, one or two lines>
→ <recommended answer>
```

One question per turn. "yes" accepts the recommendation.
