---
name: gitea-workflows
description: CI on Gitea - .gitea/workflows pipelines, test-tier selection, the compose --check job, branch model, branch protection and PR conventions. Package-monorepo publishing goes to package-publishing.md.
---

# Gitea workflows & git conventions

Package monorepo publishing (PACKAGES): [package-publishing.md](package-publishing.md).

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

## Images

`docker-image` builds one image per app, never per instance (`config-led-deployment`), passes the build secrets `gitea_user`, `gitea_token`, `gitea_host` and `gitea_package_owner` to BuildKit, checks the image's `ENTRYPOINT` file is executable (`ci/check-entrypoint.sh`, no app config needed), and scans with trivy: a fixable CRITICAL fails the job, HIGH ones are listed. Both run before the push. The runner shares the host's Docker, where deployed stacks run from the same tags, so the push (`ci/push-image.sh`) leaves every host tag on the image it had. Images follow the package channels: a push to `prep` publishes `:prep` and `:prep-<sha>`, a `vX.Y.Z` tag on `main` publishes `:X.Y.Z`. The account behind `PKG_WRITE_TOKEN` needs write on the org's packages.

An image that can be started on its own can have a smoke test: the repo passes `smoke-test: <path>` and `docker-image` runs it with the built image's tag before the push. The script starts the image (and any stub it needs) on a throwaway Docker network, makes its requests from another container on that network, never through host ports (a CI job is a sibling container on the runner's Docker, so the host's loopback is out of reach), cleans up after itself, and exits non-zero on a failure. Names carry a random suffix and everything carries the label `datumpin.ci-run=$CI_RUN_LABEL` (the step sets it), since concurrent jobs share the runner's Docker; every wait has a timeout, and a final step removes whatever carries the label (`ci/clean-run.sh`). DEVKIT's `ci/tests/smoke-example.sh` is the shape to copy.

## Test suite job

- Trigger on `pull_request`.
- One parallel job per service or component.
- Run `python -m pytest -m "unit or integration"`. Contract tests need a live dependent service and stay out of CI.
- Where compose files are generated, a separate job runs `python scripts/compose.py --check`, so a stale generated file fails the PR (see `config-led-deployment`).
- `node-tests` installs npm 11.20.0 (Node 20's npm 10 crashes on the `@datumpin` peer dependencies) and runs the production build when there is one.
- Each shared workflow opens with a header comment: what it does, why, and how a repo calls it (`code-comments-and-docstrings`).

## Branches and PRs

A repo with more than one contributor gets a short `CONTRIBUTING.md` or a root README section covering:

- Branch naming: `<type>/<issue>-<slug>` (see `formats`), or `<type>/<slug>` without a ticket.
- Who reviews a PR before merge.
- Whether CI must pass before merge.
- Commit message policy. Datumpin repos add no AI-attribution trailers, set in each `CLAUDE.md`.

A ticket that builds on another ticket's unmerged branch waits for that PR to merge, then branches from `prep`. When waiting blocks the work, stack instead: branch from the other branch, rebase onto `prep` once it merges, and open the PR after the rebase, its Summary starting `Stacked on #N` (`formats`).

## Environments

Work moves dev → prep → prod, and only through PRs and images. This table is the one place that names them; the other skills link here.

| Environment | Host | Branch | Image | Compose | Env file |
|---|---|---|---|---|---|
| dev | The laptop, Docker Desktop | A ticket branch | Built locally from `Dockerfile.dev`, tagged `:dev` | `docker-compose.dev.yml` | `.env.<app>-<instance>.dev` |
| prep | Hammond, internal staging | `prep` | `:prep`, pulled | `docker-compose.yml`, `CHANNEL=prep` | `.env.<app>-<instance>` on the host |
| prod | External server, not built yet | `main`, tag `vX.Y.Z` | `:X.Y.Z`, pulled | `docker-compose.yml`, `CHANNEL=prod` | `.env.<app>-<instance>` on the host |

- Everything runs in containers. A host holds Docker, git and its env files; the laptop also holds the agent tooling (Claude Code, `tea`, the plugin's `dp` through pipx, and the Python that the plugin's status hook, `hooks/hooks.json`, runs), the one exemption.
- Builds and tests run in dev before the push, and CI runs them again. Servers pull images; they never build or run tests.

## Branch model and protection

| Branch | Role | Protection |
|---|---|---|
| `prot/<topic>` | Exploratory spikes, in dev | None |
| `prep` | Default branch and trunk; deployed to prep | Standard rule |
| `main` | Customer release | Standard rule; only the Owners team merges |
| `<type>/<issue>-<slug>` | One ticket, short-lived | None |

The standard rule, applied under the repo owner's own login (an admin action): `tea api --login <owner> repos/R/branch_protections -X POST -d @rule.json`, and `-X PATCH` on `repos/R/branch_protections/<rule_name>` to change it. With it, the repo deletes a PR's branch when the PR merges: `tea api --login <owner> repos/R -X PATCH -d '{"default_delete_branch_after_merge":true}'`.

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
- **Approved versions, every PR, blocking:** the `versions` job fails when a listed package is pinned to another version than the master copies in DEVKIT `ci/master/` (`DRIFT` minor or patch, `MAJOR` major). Unlisted packages are counted, and osv-scanner covers them until they are listed.
- **What ships, on image build:** the image's CycloneDX SBOM goes to OWASP Dependency-Track when the org variable `DEPENDENCY_TRACK_URL` is set.

A master copy changes only through a DEVKIT PR: the new version is reviewed in Dependency-Track first, and an Owner approves the PR. The repos then conform: master first, never a repo-only upgrade of a listed package.

## Merge gate

A PR merges when:

- The tests passed in dev before the push (`testing-conventions`, The local loop), and CI passes (or the README states which checks do not block yet).
- `change-review` has run on the PR's diff, and a named human has adjudicated each finding.
- The `definition-of-done` change checklist is ticked, with the evidence in the PR description.

A promotion PR (`prep` → `main`) also runs `security-review`, completes the WIKI review worksheet, and closes on a named person's sign-off. Promotion PRs need the branching process to exist first, and the worksheet is the process until then.

## Done when

- `actionlint .gitea/workflows/*.yml` is clean (name the files explicitly, since it looks in `.github/workflows` by default).
- Each workflow folder has a README.
- Repos with generated compose files have a `compose.py --check` job.
- The test job selects `unit or integration` only.
- `prep` and `main` carry the standard protection rule.
