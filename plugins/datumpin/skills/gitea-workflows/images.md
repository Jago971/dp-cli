# Images and the test suite job

What `docker-image` and the test workflows do. Parent: [SKILL.md](SKILL.md).

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
