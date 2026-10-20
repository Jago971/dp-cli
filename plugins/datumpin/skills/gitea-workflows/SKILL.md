---
name: gitea-workflows
description: CI on Gitea - .gitea/workflows pipelines, test-tier selection, the compose --check job, branch model, branch protection and PR conventions. Package-monorepo publishing goes to package-publishing.md.
---

# Gitea workflows & git conventions

Package monorepo publishing (PACKAGES): [package-publishing.md](package-publishing.md).

## Workflows

`.gitea/workflows/` uses the GitHub-Actions-compatible dialect through a Gitea Actions runner. One folder per concern, each with a `README.md` (`test_suite/`, `dependency_tracking/`, `keyword_scanning/`). Pin action versions (`actions/checkout@v4`).

## Test suite job

- Trigger on `pull_request`.
- One parallel job per service or component.
- Run `python -m pytest -m "unit or integration"`. Contract tests need a live dependent service and stay out of CI.
- Where compose files are generated, a separate job runs `python scripts/compose.py --check`, so a stale generated file fails the PR (see `config-led-deployment`).
- State interim CI limits in the workflow README, such as "reports pass/fail but does not block merging yet" or "secret X must exist before this step passes".
- Homegrown checks (outdated-dependency checker, keyword scanner) carry a README with scope and comments following `code-comments-and-docstrings`.

## Branches and PRs

A repo with more than one contributor gets a short `CONTRIBUTING.md` or a root README section covering:

- Branch naming: `<type>/<issue>-<slug>` (see `formats`), or `<type>/<slug>` without a ticket.
- Who reviews a PR before merge.
- Whether CI must pass before merge.
- Commit message policy. Datumpin repos add no AI-attribution trailers, set in each `CLAUDE.md`.

## Branch model and protection

| Branch | Role | Protection |
|---|---|---|
| `prot/<topic>` | Exploratory spikes, on laptops | None |
| `prep` | Default branch and trunk; deployed to Hammond | Standard rule |
| `main` | Customer release | Standard rule; only the Owners team merges |
| `<type>/<issue>-<slug>` | One ticket, short-lived | None |

The standard rule, applied under the repo owner's own login (an admin action): `tea api --login <owner> repos/R/branch_protections -X POST -d @rule.json`, and `-X PATCH` on `repos/R/branch_protections/<rule_name>` to change it.

```json
{
  "rule_name": "prep",
  "enable_push": false,
  "enable_force_push": false,
  "required_approvals": 1,
  "dismiss_stale_approvals": true,
  "block_on_rejected_reviews": true,
  "block_admin_merge_override": false,
  "enable_status_check": false,
  "status_check_contexts": []
}
```

`main` takes the same rule with `"rule_name": "main"`, `"enable_merge_whitelist": true` and `"merge_whitelist_teams": ["Owners"]`.

- One approval means every agent PR needs a human's approval before it merges. A repo admin can override the approval on their own PR.
- Required checks: `"enable_status_check": true` with `"status_check_contexts": ["CI / *"]`, which requires every job of the repo's `ci.yml` (Gitea matches the pattern against `CI / <job> (pull_request)`). A repo with its own test workflow adds it (PACKAGES: `"Test Suite / *"`).
- A repo whose work still lands directly on `main` takes the rule at onboarding, after its work moves to `prep`.

## Dependency versions

Three checks, each covering what the others do not:

- **Known vulnerabilities, every PR, blocking:** osv-scanner in DEVKIT's `security-scan`.
- **Approved versions, every PR, reporting only:** the `versions` job compares each repo's pins with the master copies in DEVKIT `ci/master/` (`DRIFT` for a minor or patch difference, `MAJOR` for a major one). It never fails a PR.
- **What ships, on image build:** the image's CycloneDX SBOM goes to OWASP Dependency-Track when the org variable `DEPENDENCY_TRACK_URL` is set.

A master copy changes only through a DEVKIT PR: the new version is reviewed in Dependency-Track first, and an Owner approves the PR.

## Merge gate

A PR merges when:

- CI passes (or the README states which checks do not block yet).
- `change-review` has run on the PR's diff, and a named human has adjudicated each finding.
- The `definition-of-done` change checklist is ticked, with the evidence in the PR description.

A promotion PR (`prep` → `main`) also runs `security-review`, completes the WIKI review worksheet, and closes on a named person's sign-off. Promotion PRs need the branching process to exist first, and the worksheet is the process until then.

## Done when

- `actionlint .gitea/workflows/*.yml` is clean (name the files explicitly, since it looks in `.github/workflows` by default).
- Each workflow folder has a README.
- Repos with generated compose files have a `compose.py --check` job.
- The test job selects `unit or integration` only.
- `prep` and `main` carry the standard protection rule.
