---
name: align
description: Align - find drift between where a repo is (code, CHANGELOG), where it planned to go (Gitea tickets, milestones) and where it is heading (roadmap, plan docs, decisions), then fix it. Use when a repo joins the workflow, after a decision changes direction, when a milestone closes, or when asked to check or clean up the backlog.
model: opus
effort: high
---

# Align

Three positions, each with its own source of truth:

| Position | Read from |
|---|---|
| **Where we are** | Code, `docs/log/CHANGELOG.md`, closed tickets |
| **Where we planned to go** | Open tickets and milestones in Gitea |
| **Where we are heading** | `docs/plan/ROADMAP.md`, plan docs, the decision log, and sibling repos' plans that need work here |

**Drift** is any gap between them. Each finding is one of five kinds:

| Kind | Means | Usual action |
|---|---|---|
| `DONE-OPEN` | A ticket is open but the code or CHANGELOG shows it shipped | Close with a pointer |
| `OFF-COURSE` | A ticket no longer matches the direction | Re-scope, re-milestone, or close with a pointer |
| `NO-TICKET` | The direction or a sibling repo needs work nothing tracks | Draft a ticket |
| `NO-DIRECTION` | A ticket nothing in the docs supports | Ask: keep in Triage, record the direction, or close |
| `DOCS-BEHIND` | A doc lists done work as open, or contradicts the code | A doc fix in a PR |

Use the `gitea` skill for every call and the `formats` skill for everything printed or written, including its Quiet steps rule.

## Modes

- **Reset**: the repo's tickets predate the workflow (the repo has no `Board`, or most open tickets are not on it). Every old ticket is closed with a pointer; what is still valid is carried into new tickets; the roadmap becomes direction plus milestones; the board and component labels are set up.
- **Review**: the backlog is already in the workflow. Only the drift found changes.

Pick the mode from the labels and say which in the drift report.

## Steps

1. **Config.** Read the plugin defaults at `../../defaults/flow.yaml` (relative to this skill's base directory), then the repo's `.claude/flow.yaml`; repo keys win.
2. **Review.** Dispatch three read-only subagents in one message, each with the model and effort in `align.review`, each returning its report shape below:
   - **Tickets:** every open ticket and milestone, checked against the code, CHANGELOG and docs.
   - **Own docs:** the open work and open decisions in this repo's roadmap, plan docs and decision log, checked against the CHANGELOG; plus any doc that contradicts the code.
   - **Siblings:** the docs of the other repos in the Gitea team `Agents`, for work they need from this repo or are waiting on it for.
3. **Report.** Merge the three into one drift report. Write the full findings and the proposed changes to `.factory/align-<YYYY-MM-DD>.md`, and print the drift report.
4. **Draft.** Turn the accepted kinds into: milestones and tickets (as `shape` drafts them), pointer comments for closures, label and milestone moves, and doc fixes. In Reset mode, also draft: the roadmap rewrite (direction in order, the milestones, standing decisions; the old roadmap moves unchanged to `docs/_archive/ROADMAP_<YYYY-MM-DD>.md`); the repo's `components` for `.claude/flow.yaml`, one per top-level code folder, if it has none; the list of old projects to close; and a ticket for each onboarding check that fails (steps 5 to 8 of the plugin README's onboarding list: root `skills/` copy, default branch and protection, CI, host deploy keys). Show the draft list and the closure count, and apply edits until the user says yes.
5. **Write.** In this order, one log line each:
   1. In Reset mode, the `Board` project with its seven columns (Triage the default) and the `COMPONENT/*` repo labels, as the agent login.
   2. Milestones, then tickets, each placed in its column, as the agent login. Later tickets link earlier ones as `#N`.
   3. Label, milestone and column moves, as the agent login.
   4. As the user's own login (the default `tea` login), since these are human or admin actions: a pointer comment then close for each old ticket; close each old project; set `prep` as the default branch and apply the standard protection rule (`gitea-workflows`) to `prep` and `main`, when the repo's work already lands on `prep`.
   5. Doc fixes, the roadmap rewrite and `.claude/flow.yaml` on a `docs/<slug>` branch, with a CHANGELOG entry, opened as a PR by the agent login.
6. **Summary.** Print one `DONE` log line with the counts, then a numbered list of what is left for the user (merge the PR), then the To-close list (`formats`) of the superseded tickets the user chose not to close in step 5.4.

## Subagent report shapes

**Tickets**, one row per open ticket:

| # | Title | Verdict | Why (one line, cite file or doc) | Carry forward |
|---|---|---|---|---|

Verdict is `COVERED`, `OBSOLETE`, `PARTLY` or `STILL-VALID`. Then the milestones found, and a two-line summary.

**Own docs**: themes with a one-line goal and source; under each, candidate tickets as `title | what and why | TYPE | size | depends on | source | DECISION?`; then the open decisions; then each doc that contradicts the code or CHANGELOG.

**Siblings**: grouped by repo, each item as `title | what and why | source file and heading | already done here?`; then what each sibling is waiting on.

## Done when

- Every open ticket has a verdict, and every theme in the plan docs has a ticket or a recorded reason it has none.
- Every write was accepted by the user and printed as a log line.
- In Reset mode, no pre-workflow ticket or project is left open, every open ticket is on the board, and the roadmap PR is open.
