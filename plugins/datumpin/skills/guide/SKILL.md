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
ticket: 52   # a number; anything else is ignored
updated: 2026-10-21T16:40:00
```

## Steps

1. **Read.** Read the map and the state file. With no state, a state the map does not know, or a finished flow, offer the flows from the map as choices, and take the user's pick.
2. **Check the position.** In the ticket flow, read the ticket's board column (`gitea`) and trust it over the state file, printing a log line when it corrects the state:

   | Column | Position |
   |---|---|
   | Triage | `shape` |
   | Backlog | `pick` |
   | In Progress | the state's step when it is `build` to `fix`, else `build` |
   | Review | the state's step when it is `fix` or `pr`, else `merge` |
   | Testing | `try` |
   | DoD | the release flow, at `review` |
   | Done | the session flow, at `board` |

   The release, deploy and session flows carry no ticket and trust the state file. When Gitea is unreachable, print one log line and go on from the state file.
3. **Offer.** Print the Guide prompt (`formats`). The choices are the step's `next` and `optional` steps that the current flow lists, then its `fork`s, then `stop`.
4. **Run.** On a choice, run the step:
   - a skill: call the Skill tool with it and the ticket as the argument; the skill decides its own output and prompts.
   - a user-invoked skill (`handoff`, `retro`): print the command for the user to type.
   - `agent`: do the step directly, in its `formats` shape.
   - `human`: print what the person does, and wait for them to say it is done.

   After `shape`, ask which of its tickets to pick. Offer `tag` only once the release PR is merged on `main` (`gitea`); a state file alone never reaches it.
5. **Record.** Write the new position to the state file, then go back to step 3. On `stop`, write the state and end with one log line naming where to resume.

## Done when

- Every step ran only after the user chose it.
- The state file names the position the session ended on.
