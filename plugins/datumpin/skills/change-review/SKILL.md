---
name: change-review
description: Review a diff on two separate axes, Standards and Spec, using parallel subagents. Use when reviewing a branch, a PR or work in progress, or asked to review since a commit.
---

# Change review

Output follows `formats`, including its Quiet steps rule.

Review the diff from a fixed point to `HEAD` on two axes, run by **parallel subagents** so neither pollutes the other's context:

- **Standards:** does the code follow this repo's documented standards (its skills and docs)?
- **Spec:** does the code do what was asked, no more and no less?

A change can pass one axis and fail the other, so the report keeps them separate and never merges or reranks them.

## Process

1. **Pin the fixed point.** Use the commit, branch or tag the user names, and ask when none is given. Run `git rev-parse <fixed-point>` and `git diff <fixed-point>...HEAD`, and note `git log <fixed-point>..HEAD --oneline`. Stop here when the ref does not resolve or the diff is empty.
2. **Find the spec.** In order: an issue or PR reference in the commit messages, a path the user passes, the matching expansion or section in `docs/plan/` (`REBUILD_PLAN.md`, `ROADMAP.md`, a standalone plan). With none found, ask. With none existing, skip the Spec axis and say so in the report.
3. **Find the standards.** The skills `CLAUDE.md` lists for the kinds of file in the diff (Python, compose, docs, tests, frontend), plus the repo's own reference docs. A documented repo standard decides each case.
4. **Run the reviewers, scaled to the change.** Give each the diff command, the commit list, the skill files to read (not only the diff) and a word limit.
   - Docs, skill text or config only: one reviewer covering both axes, on the model `flow.yaml` sets for `change_review.single`, under 250 words, keeping the two axes as separate headings.
   - Code: both subagents together, in the foreground, under 400 words each.
   - A promotion: both, plus `security-review` (see Security).
   - **Standards brief:** report every place the diff breaks a documented rule, citing the skill and the rule, and quote the hunk. Skip what a linter or test already enforces.
   - **Spec brief:** report requirements that are missing or partial, behaviour in the diff nobody asked for, and requirements that look implemented but wrong. Quote the spec line for each.
5. **Report** under `## Standards` and `## Spec` headings, each finding with file, line, severity and the rule or spec line. End with the finding count per axis and the worst finding within each axis.
6. **A human adjudicates.** The engineer or reviewer confirms, dismisses or escalates each finding, and the disposition is written next to it (PR comment or review note). The agent never approves its own review.

## Security

At a promotion PR (proto → prep → prod), also call the `security-review` skill on the same diff. Its findings go in a third section, `## Security`, and are adjudicated the same way (see `definition-of-done`).

## Done when

- Both axes (or the Spec skip, with its reason) are in the report.
- Every finding cites a rule or a spec line and a file and line.
- Every finding has a human disposition recorded.
