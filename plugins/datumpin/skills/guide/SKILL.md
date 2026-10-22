---
name: guide
description: Guide - walk a flow one step at a time - where you are, the step you choose, the next choices. Use when asked for the guide or to carry on a ticket or release.
model: sonnet
effort: medium
---

# Guide

Leads the user along the flows in `../../flows.yaml` (relative to this skill's base directory): the ticket flow, release, align, deploy and the session. Each step runs the skill the map names; the guide only finds the position, runs the chosen step and offers what comes next. It always stops between steps. Use the `formats` skill for everything printed, including its Quiet steps rule.

At a terminal, `dp guide` walks the same flows with no session: the person's gates are CLI prompts, and each agent step gets a job brief and a Claude session on its skill's model (plugin README, The guide at a terminal). This skill is the in-session fallback, and finds the position through `dp guide --json`, so both follow one rule.

## State

`.factory/guide.yaml` in the repo holds the position (gitignored with `.factory/`):

```yaml
flow: ticket
step: review
ticket: 52   # a number; anything else is ignored
paused_ticket: 48   # the ticket flow left for another flow, with its step
paused_step: test
updated: 2026-10-21T16:40:00
```

## Steps

1. **Position.** Run `dp guide --json` (`gitea`, Calling dp). It reads the map, the state file and, in the ticket flow, the ticket's board column, which places the ticket over the state file (the map's `columns`). It returns the `position` (null with no state, one the map does not know, or a finished flow) and its `env`, the `paused` ticket flow, `notes` (a log line for each correction, or for Gitea unreachable) and the `choices`, each `next`, `fork` (only the forks whose check holds) or `flow`. Print the notes. At `review`, ask each finding's disposition (`change-review`) before offering, and offer `fix` first when one is to fix.
2. **Offer.** Print the Guide prompt (`formats`) from the position and the choices. `flows…` offers `resume #N` when a ticket flow is paused, then the flows.
3. **Run.** On a choice, run the step:
   - `pick`: `dp pick N --json` (`gitea`), not the board flow.
   - a skill: call the Skill tool with it and the ticket as the argument; the skill decides its own output and prompts.
   - a user-invoked skill (`handoff`, `retro`): print the command for the user to type.
   - `agent`: do the step directly, in its `formats` shape.
   - `human`: print what the person does, and wait for them to say it is done.

   After `shape`, ask which of its tickets to pick. Offer `tag` only once the release PR is merged on `main` (`gitea`); a state file alone never reaches it. Leaving `test`, ask `Tested OK?`: on yes, post a Tested Pointer (`formats`, Comment) with `dp pointer`; on no, stay at `test`.
4. **Record.** Write the new position to the state file, with `paused_ticket` and `paused_step` when the choice left the ticket flow (cleared on coming back to it), then go back to step 1. On `stop`, write the state and end with one log line naming where to resume.

## Done when

- Every step ran only after the user chose it.
- The state file names the position the session ended on.
