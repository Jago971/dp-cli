# Changelog

Dated record of what changed in DEVKIT, newest first. Plugin versions are in `plugins/datumpin/.claude-plugin/plugin.json`.

---

### [CHANGED] 2026-10-21 - PRs name related tickets under See (plugin 0.6.2)

- The `formats` PR shape keeps `Refs #N` for the tickets a PR works on and adds a `See #N` line for related ones. board-sync moves only `Refs` and branch tickets, so a related ticket keeps its column (#40).

---

### [CHANGED] 2026-10-21 - board picks from the current milestone first (plugin 0.6.1)

- `board` suggests the earliest open milestone's tickets first (CRITICAL anywhere still first), then priority; the board view gains a `Milestones` line with each open milestone's progress. Its sync reads every page of each column, as board-sync does since #53.

---

### [CHANGED] 2026-10-21 - Quiet flow steps; review effort scales with the change (plugin 0.6.0)

- `formats` Quiet steps: nothing printed between tool calls while a flow step runs; the step ends with its shaped output and at most one prompt. `board`, `shape`, `align`, `tdd`, `definition-of-done`, `change-review` and `retro` point to it.
- `change-review` scales reviewers to the change: one reviewer on a smaller model for docs and skill text, two for code, both plus `security-review` for a promotion; reviewers read the skills they cite.

---

### [CHANGED] 2026-10-21 - v0.5.0 release review fixes (plugin 0.5.10)

- `docker-image`: the entrypoint check always uses main's script (the DEVKIT branch never ran), with `--network none` and a 2-minute timeout; the smoke test gets a run label (`CI_RUN_LABEL`) and a final step removes what carries it (`ci/clean-run.sh`).
- `gitea-workflows` and `smoke-example.sh`: the run label in the smoke-test contract.
- `frontend.md`: Parent line; states the backend-name rule itself. `ci.yml` comment; `ci/tests/pytest.ini` in the testing-conventions shape; test README explains the flat layout.

---

### [FIXED] 2026-10-21 - Image pushes leave the host's tags alone (plugin 0.5.9)

- `docker-image` pushed by tagging on the runner's Docker, which is Hammond's, then removed every pushed tag, untagging the `:prep` images BDS and CURATOR run from. `ci/push-image.sh` now puts each tag back on the image it had (or removes one that was not there), and the cleanup removes only the job's local tag.
- `ci/tests/test_push_image.py`: an integration test against a throwaway `registry:2`.

---

### [DOCS] 2026-10-21 - SBOMs for nginx frontends (plugin 0.5.8)

- `docker-compose-conventions` (SBOM) and `frontend.md`: every image carries `/sbom.json`; backends and dev frontends also write a dated SBOM into `./sboms` at boot; a prod nginx frontend (non-root) keeps it in the image, mounts no `./sboms`, and is read with `docker cp`. What CI sends to Dependency-Track stays in `gitea-workflows`.

---

### [DOCS] 2026-10-21 - The nginx frontend serve stage (plugin 0.5.7)

- `docker-compose-conventions/frontend.md` (new, loaded from the skill's branches) records the frontend serve stage CURATOR and AHJ use: `nginx-unprivileged` on 3000, `default.conf.template` filled at start (SPA fallback, `/api` proxy to the backend named in the instance env file, extra backend paths, `client_max_body_size`), no compose start command, branding mounted read-only. The `nginx:alpine` example is gone.

---

### [ADDED] 2026-10-21 - Images: a repo's smoke test before the push (plugin 0.5.6)

- `docker-image` takes an optional `smoke-test` input: a script in the repo, run with the built image's tag after the entrypoint check; a failure stops the push.
- `gitea-workflows` records the contract: requests from inside a Docker network, never host ports, since CI jobs are sibling containers. `ci/tests/smoke-example.sh` is the example, tested as CI runs it.
- `.gitattributes` keeps shell scripts LF, so a Windows checkout can run them.

---

### [ADDED] 2026-10-21 - Images: entrypoint check before the push (plugin 0.5.5)

- `ci/check-entrypoint.sh`: fails an image whose `ENTRYPOINT` file is missing or not executable, by running `test -x` inside it; `docker-image` runs it after the build, before the scan and push. BDS's api image shipped that fault and failed only on Hammond.
- `ci/tests/test_check_entrypoint.py`: integration tests against three tiny images.
- `gitea-workflows` Images section names the check.

---

### [FIXED] 2026-10-21 - board-sync reads every page of a column

- `ci/board_sync.py` read only the first 50 tickets of each column, so a ticket further down looked "not on the Board" and was added again instead of moved (AHJ's Backlog holds 54).
- It reads until an empty page (not a short one, so a lower server cap is fine) and stops after 40 pages if paging is ignored.
- `ci/tests/`: DEVKIT's first CI-script tests, against an in-memory Gitea (`fake_gitea.py`); `ci.yml` runs them through `python-tests`, with pytest pinned in `ci/tests/requirements.txt`.

---

### [ADDED] 2026-10-20 - Images, publishing and the version lock (plugin 0.5.3, 0.5.4)

- `docker-image`: one image per app, BuildKit secrets, trivy (a fixable CRITICAL fails), `:prep` and `:prep-<sha>` from `prep`, `:X.Y.Z` from a release tag; BDS, AHJ (backend) and CURATOR publish through it.
- `publish-python`, `publish-npm` and `ci/release-channel.sh` (moved from PACKAGES); PACKAGES' publish jobs call them.
- `ci/master/` (moved from WIKI, revised where osv flagged a master version) and the blocking `versions` job in `security-scan`; DEVKIT checks itself with its own script.
- `node-tests` installs npm 11.20.0 and runs the production build.
- Skills: `gitea-workflows` describes the shared CI files, images and dependency versions; `package-publishing` the shared publish jobs; `config-led-deployment` rollout deploys from images.

### [ADDED] 2026-10-20 - Board sync, npm fix, runner capacity 2

- `board-sync` shared workflow and `ci/board_sync.py`: tickets move to Review when a PR naming them opens, to Testing when it merges into `prep`, to Done when closed (#26). Every repo calls it from `board.yml`; conformance checks it.
- `node-tests` installs npm 11.20.0: Node 20's npm 10 crashed resolving the `@datumpin` packages' peer dependencies.
- The runner runs two jobs at once ([runner.md](../runner.md)).

### [ADDED] 2026-10-20 - Conformance check, diagrams rule, DEVKIT's own docs (plugin 0.5.1)

- `conformance` shared workflow and `ci/conformance.py`: a repo fails CI when it drifts from the standard use of the plugin and workflow.
- `claude-md-authoring`: CLAUDE.md opens with the same four sections in every repo. `documentation-cross-cutting`: Mermaid diagrams. `quickstart-guide`: the map may be a diagram.
- DEVKIT's own QUICKSTART, docs index, roadmap and this changelog; its CI also runs actionlint, plugin validation and conformance.

### [ADDED] 2026-10-20 - Findings loop and session status line (plugin 0.5.0)

- Plugin and CI findings from any repo become DEVKIT Triage tickets; `retro` drafts tickets; a session-start hook prints Triage counts and open PRs.

### [ADDED] 2026-10-20 - Shared CI: tests, compose check, security scan

- Reusable workflows `python-tests`, `node-tests`, `compose-check` and `security-scan` (gitleaks, osv-scanner), called `@main` with the org registry secrets.
- The Actions runner on Hammond moved to `gitea/runner:5` ([runner.md](../runner.md)); Docker there trusts the plain-HTTP registry.

### [ADDED] 2026-10-20 - DEVKIT created

- The `datumpin` plugin (0.4.0) and its marketplace moved here from WIKI `main` at `d91ab23`; consumers install from DEVKIT `main`.
