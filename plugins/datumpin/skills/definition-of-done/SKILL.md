---
name: definition-of-done
description: Done - the checklist a change passes before it is finished or opened as a PR. Use when finishing work, before a closing commit, or asked if it is done.
---

# Definition of done

Output follows `formats`, including its Quiet steps rule.

A change is done when every applicable item below is checked with evidence (a command's output, a file path). An item that does not apply is marked n/a with a reason.

Three levels use the same idea:

| Level | Checked by | Where |
|---|---|---|
| Step done | the agent, at the end of each skill step | the "Done when" of each skill |
| **Change done** | the engineer, then `change-review` | this skill |
| Promotion done (dev → prep → prod, `gitea-workflows` Environments) | engineer, reviewer, security, with sign-off | the worksheet in WIKI `business_processes/reviews/templates/software_lifecycle_review_checklist.md` |

## Change checklist

**Standards** (each skill owns its rules)
- [ ] Comments and docstrings follow `code-comments-and-docstrings`.
- [ ] Config and secrets follow `secrets-handling` (no secret in git or an image layer).
- [ ] Docker and compose edits follow `docker-compose-conventions`, and `python scripts/compose.py --check` exits 0 where compose files are generated.
- [ ] Code follows the layering skill for its area (`fastapi-service-architecture`, `react-frontend-architecture`).

**Behaviour**
- [ ] New behaviour has `unit` or `integration` tests (`testing-conventions`), written at agreed seams (`tdd`).
- [ ] A bug fix has a regression test that failed before the fix (`diagnosing-bugs`).
- [ ] The tests pass in the dev container before the push (`testing-conventions`, The local loop); CI runs them again.
- [ ] Errors raise specific exceptions with clear messages, inputs are validated at the boundary, and logs carry no secrets or personal data.
- [ ] A change that adds a schema column has its Alembic revision (`alembic-migrations`).

**Documentation** (`documentation-cross-cutting`)
- [ ] The folder README and the `docs/README.md` index match the change.
- [ ] A shipped change has a CHANGELOG entry.
- [ ] A hard-to-reverse, surprising trade-off has a decision-log entry (`domain-modeling`).
- [ ] A new or sharpened term is in `GLOSSARY.md`.

**Process**
- [ ] While the old and new builds run in parallel, a bug fix is in both, and the fix and its test are logged in `docs/plan/SHARED_LIBRARY_TRIAGE.md`.
- [ ] A changed skill ships with a plugin version bump (plugin README, Releasing a change).
- [ ] A promotion to `main` pins no pre-release package version (`gitea-workflows` package-publishing).
- [ ] `change-review` has run, and a named human has adjudicated its findings.

## Promotion gate

A promotion PR (dev → prep → prod) adds the full worksheet: Stage 1 orientation, Stage 2 quality, Stage 3 security, the meta-review, the final decision and the sign-off table. An independent `change-review` pass and the `security-review` skill run first and fill the Rev and Sec columns with findings, and the reviewer and security owner confirm, dismiss or escalate each. The gate closes when a named person signs. The model never signs for itself.

## Done when

- Every box above is checked with evidence or marked n/a with a reason.
- The PR description's `Review` section (`formats`) lists the evidence (test count, `--check` result) and the review findings with their dispositions.
