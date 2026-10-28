---
name: gitea-workflows
description: CI on Gitea - .gitea/workflows, test tiers, images, environments, branch protection, PR merge gate. Use when writing a workflow or changing branches.
---

# Gitea workflows & git conventions

Branches that load a sibling file:

- Building and smoke-testing an image, or the test suite job: [images.md](images.md).
- The dev, prep and prod environments, the branch model and its protection rule: [environments.md](environments.md).
- Dependency versions and the master copies: [dependencies.md](dependencies.md).
- Package monorepo publishing (PACKAGES): [package-publishing.md](package-publishing.md).

## Workflows

`.gitea/workflows/` uses the GitHub-Actions-compatible dialect through a Gitea Actions runner (DEVKIT `docs/runner.md`). Every repo runs DEVKIT's shared workflows, called `@main` with `secrets: inherit`, from three short files:

| File | Trigger | Calls |
|---|---|---|
| `ci.yml` | `pull_request` | `python-tests` or `node-tests` per service, `compose-check`, `security-scan` (gitleaks, osv-scanner, `versions`), `conformance` |
| `board.yml` | PR opened, reopened, closed; issue opened, closed, reopened | `board-sync` |
| `image.yml` | push to `prep`, `v*` tags | `docker-image`, once per app |

A repo keeps a workflow of its own only for what no shared one does (PACKAGES' `test_suite/test.yml` tests only the packages a PR touches). Credentials are org secrets (`PKG_USER`, `PKG_READ_TOKEN`, `PKG_WRITE_TOKEN`, `BOARD_TOKEN`) and variables (`PKG_REGISTRY_HOST`, `PKG_REGISTRY_OWNER`); the read token installs, only image and package publishing use the write token. Pin action versions (`actions/checkout@v4`) and tool binaries (version plus SHA-256).

A change to a shared workflow is tested on its DEVKIT PR, or from a consumer branch that points at the DEVKIT branch, then released (`prep` → `main`); a consumer never pins a branch, and `conformance` fails one that does. Merge the feature PRs into DEVKIT `prep` before opening the release PR.

`conformance` fails a PR that names no local ticket and has no `No ticket:` line (`formats`). A re-run reads the PR as it was opened, so after fixing the description, close and reopen the PR.

## Branches and PRs

A repo with more than one contributor gets a short `CONTRIBUTING.md` or a root README section covering:

- Branch naming: `<type>/<issue>-<slug>` (see `formats`), or `<type>/<slug>` without a ticket.
- Who reviews a PR before merge.
- Whether CI must pass before merge.
- Commit message policy. Datumpin repos add no AI-attribution trailers, set in each `CLAUDE.md`.

A ticket that builds on another ticket's unmerged branch waits for that PR to merge, then branches from `prep`. When waiting blocks the work, stack instead: branch from the other branch, rebase onto `prep` once it merges, and open the PR after the rebase, its Summary starting `Stacked on #N` (`formats`).

## Merge gate

A PR merges when:

- The tests passed in dev before the push (`testing-conventions`, The local loop), and CI passes (or the README states which checks do not block yet).
- `change-review` has run on the PR's diff, and a named human has adjudicated each finding.
- The `change-ready` change checklist is ticked, with the evidence in the PR description.

A release PR per milestone (`prep` → `main`) ships the signed milestone; its merge is tagged `vX.Y.Z`. It also runs `security-review`, completes the WIKI review worksheet, and closes on a named person's sign-off. Promotion PRs need the branching process to exist first, and the worksheet is the process until then.

## Done when

- `actionlint .gitea/workflows/*.yml` is clean (name the files explicitly, since it looks in `.github/workflows` by default).
- Each workflow folder has a README.
- Repos with generated compose files have a `compose.py --check` job.
- The test job selects `unit or integration` only.
- `prep` and `main` carry the standard protection rule.
