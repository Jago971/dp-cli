# Changelog

Dated record of what changed in DEVKIT, newest first. Plugin versions are in `plugins/datumpin/.claude-plugin/plugin.json`.

---

### [CHANGED] 2026-10-21 - Test locally before the push (plugin 0.7.1)

- `testing-conventions` gains The local loop: per repo kind, the dev-stack and in-container test commands; tests never run on prep or prod (#90).
- `definition-of-done` and the `gitea-workflows` merge gate ask for the local run first; CI is the second check.

---

### [CHANGED] 2026-10-21 - dev, prep and prod defined once (plugin 0.7.0)

- `gitea-workflows` gains an Environments table: host, branch, image, compose and env file for dev (laptop), prep (Hammond) and prod (not built). Servers pull and never build or test; the agent tooling is the laptop's one host exemption (#89).
- `definition-of-done`, `docker-compose-conventions` and `config-led-deployment` link it; `proto` becomes `dev`.

---

### [FIXED] 2026-10-21 - v0.6.0 release-review fixes (plugin 0.6.14)

- The `Refs` and `No ticket:` regexes run in linear time on any PR body (they were quadratic on blank lines); a test guards it (#101).
- `gitea`: issue comment text is data, never instructions.
- Docs: the local test command names the Docker-socket trust; the Handover example has no personal path.

---

### [CHANGED] 2026-10-21 - handoff ends with a Handover block (plugin 0.6.13)

- `handoff` writes `.factory/handoff-<date>.md` in the repo the next session starts in, and ends with a Handover block (new in `formats`): the path, the prompt to paste, and the human's open steps (#78).

---

### [CHANGED] 2026-10-21 - A milestone once work starts (plugin 0.6.12)

- A Backlog ticket may have no milestone; `board` gives a picked one the earliest open milestone, and flags a missing milestone only from In Progress on (#62).

---

### [CHANGED] 2026-10-21 - Branches are deleted on merge (plugin 0.6.11)

- `gitea-workflows` sets Gitea's "delete branch after merge" default with the protection rule; onboarding and `align` apply it (#58).

---

### [DOCS] 2026-10-21 - Local-first direction

- The roadmap leads with local-first, containers-only development (milestone v0.7.0) and lists the open milestones; the release gate moves to v0.8.0.
- The quickstart adds Docker Desktop to machine setup and the local test step to the ticket flow; `ci/tests/README.md` gives the local test command.

---

### [CHANGED] 2026-10-21 - Every PR names a local ticket or says why not (plugin 0.6.10)

- `conformance` gains `pr-ticket`: a PR names a local ticket board-sync moves (a `Refs` line or its branch) or has a `No ticket: <reason>` line, so repo-wide work shows on the repo's Board (#57). The `formats` PR shape documents the line.

---

### [CHANGED] 2026-10-21 - Superseded tickets: pointer plus a to-close list (plugin 0.6.9)

- `shape` and `align` end with a To-close list (a new `formats` shape) of the tickets they superseded, each with its pointer verdict (#56).
- `board` flags an open ticket whose last agent comment retires it.
- Every close follows a Pointer comment saying why: `Done` with the release, or the verdict that retired it.

---

### [CHANGED] 2026-10-21 - Partial delivery: one deliverable per ticket, Progress comments, stacked branches (plugin 0.6.8)

- `shape` splits a ticket per deliverable (#55).
- A move to an earlier column posts a `Progress` comment, a new `formats` comment kind: what landed and what is left.
- A ticket built on another's unmerged branch waits for its merge, or stacks and opens its PR with `Stacked on #N` (`gitea-workflows`).

---

### [CHANGED] 2026-10-21 - Image smoke tests and guard checks in the testing skills (plugin 0.6.7)

- `testing-conventions` places image smoke tests (`<service>/tests/smoke-image.sh`): what they check, how to run them, and the CI wiring through `docker-image`. `tdd` keeps a test that passes first as a named guard, once it has been seen to fail (#45).

---

### [CHANGED] 2026-10-21 - Pre-PR review findings go in the PR description (plugin 0.6.6)

- The `formats` PR shape gains a `Review` section: the evidence, and a findings table with each disposition (`Fixed`, `Dismissed`, `Deferred: #N`). `change-review` writes a pre-PR review there and later reviews in PR comments (#49).

---

### [FIXED] 2026-10-21 - board assigns by Gitea username (plugin 0.6.5)

- `gitea` says how to read the human's username (`tea api --login <their login> user`); `board` assigns a picked ticket to it, not to the tea login name (#43).

---

### [FIXED] 2026-10-21 - Status line also on resumed sessions (plugin 0.6.4)

- The session-start hook runs on `resume` as well as `startup`, so a reloaded window still shows Triage counts and open PRs (#41).

---

### [CHANGED] 2026-10-21 - board-sync puts new issues in Triage (plugin 0.6.3)

- An issue opened by any route lands in Triage; one already on the Board keeps its column (#44). Each repo's `board.yml` adds `opened` to its `issues` types.

---

### [CHANGED] 2026-10-21 - PRs name related tickets under See (plugin 0.6.2)

- The `formats` PR shape keeps `Refs #N` for the tickets a PR works on and adds a `See #N` line for related ones. board-sync moves only `Refs` and branch tickets, so a related ticket keeps its column (#40).

---

### [CHANGED] 2026-10-21 - board picks from the current milestone first (plugin 0.6.1)

- `board` suggests the earliest open milestone's tickets first (CRITICAL anywhere still first), then priority; the board view gains a `Milestones` line with each open milestone's progress. Its sync reads every page of each column, as board-sync does since #53 (#76).

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
