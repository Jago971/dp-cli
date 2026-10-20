---
name: shape
description: Shape - turn an idea, feature request or vague ticket into scoped Gitea tickets, or group features into a milestone. Use when scoping or planning a feature or release, or refining a ticket.
model: opus
effort: high
---

# Shape

Turns loose intent into tickets an agent can build from, through a short interview. Use the `gitea` skill for every call and the `formats` skill for everything printed or written.

## Steps

1. **Level.** `shape #N` refines ticket N (step 7). Otherwise it is **feature** level, or **release** level when the user names several features, a release or a milestone. Ask only when it is unclear.
2. **Facts.** Read the repo's `CLAUDE.md`, `docs/plan/ROADMAP.md`, the open issues and the code the idea touches. Dispatch an Explore subagent for wide searches. Look facts up yourself; put only decisions to the user. Name any open issue that overlaps.
3. **Interview.** Map the decisions as a design tree, the way `grilling` does, but ask one shaping question per turn, each with your recommendation. The tree is settled when these are known: what changes and for whom, acceptance, out of scope, priority, stage (`PROT` or `PREP`), and milestone.
4. **Draft.** Write each ticket in the ticket-body format. Split so each ticket is one PR: small and mergeable alone. Labels: one `TYPE`, one `PRIORITY`, one `STAGE`, `ORIGIN/AGENT`, and the `COMPONENT` of each folder the ticket touches (the repo's `components` config). Column: Backlog, or Triage while a question stays open. At release level, draft the milestone too, in the milestone shape; the version is the next minor after the highest existing one unless the user names it.
5. **Review.** Show the draft list. Apply each edit or drop, and show it again, until the user says yes.
6. **Push.** As the agent login: the milestone first, then each issue in order, each placed in its board column, one log line each. If Gitea is unreachable, save each draft to `.factory/outbox/<slug>.md`, print a `FAILED` log line, and stop; `board` pushes the outbox later. An outbox file is:

   ```
   title: <title>
   labels: <comma-separated>
   column: <Backlog or Triage>
   milestone: <title or empty>
   ---
   <ticket body>
   ```

7. **Refine #N.** Read the issue and its comments, run steps 2 and 3 on it, then post one Scope comment (see `formats`). Move it to Backlog and add its `TYPE`, `PRIORITY`, `STAGE` and `COMPONENT` labels when settled; add `STATUS/NEEDS-INFO` when a question is still open. The body changes only if the agent login wrote it.

## Done when

- The interview covered every item in step 3, each decided by the user.
- Every approved ticket and milestone exists in Gitea, or in the outbox, with its labels and milestone.
- A log line was printed for each write.
