---
name: guide
description: Guide - walk a flow one step at a time from the flow map - where you are, run the step you choose, then offer the next choices. Use when asked for the guide, what to do next in a flow, or to carry on a ticket, a release or a session.
model: sonnet
effort: medium
---

# Guide

Leads the user along the flows in `../../flows.yaml` (relative to this skill's base directory): the ticket flow, release, align, deploy and the session. Each step runs the skill the map names; the guide only finds the position, runs the chosen step and offers what comes next. It always stops between steps. Use the `formats` skill for everything printed, including its Quiet steps rule.

## State

`.factory/guide.yaml` in the repo holds the position (gitignored with `.factory/`):

```yaml
flow: ticket
step: review
ticket: 52
updated: 2026-10-21T16:40:00
```

## Steps

1. **Read.** Read the map and the state file. With no state, offer the flows from the map as choices, plus `board`, and take the user's pick.
2. **Check the position.** For the ticket flow, read the ticket's board column (`gitea`) and trust it over the state file when they disagree: In Progress is `build` to `fix`, Review is `pr`, Testing is `merge` or `try`. Say so in a log line when it corrects the state.
3. **Offer.** Print the Guide prompt (`formats`): the position, the last step's outcome, and the choices. Choices are the step's `next` steps the current flow lists, its `optional` steps, its `fork`s (a fork into another flow names it), and `stop`, always last.
4. **Run.** On a choice, run the step: call the Skill tool with the step's `skill` and the ticket as its argument, or, for a `human` step, print what the person does and wait for them to say it is done. The step's own skill decides its output and its prompts.
5. **Record.** Write the new position to the state file, then go back to step 3. On `stop`, write the state and end with one log line naming where to resume.

## Done when

- Every step ran only after the user chose it.
- The state file names the position the session ended on.
