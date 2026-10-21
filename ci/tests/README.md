# ci/tests/

**Scope:** tests for the CI scripts in `ci/`, run by DEVKIT's `ci.yml` through the shared `python-tests` workflow (`working-directory: ci/tests`). 23 tests: 14 `unit`, 9 `integration` (need a Docker daemon; skipped without one).
**Status:** current
**Last reviewed:** 2026-10-21
**Governed by:** [docs/QUICKSTART.md](../../docs/QUICKSTART.md)

---

`fake_gitea.py` is an in-memory Gitea Board: it answers the calls `board_sync.py` makes through `call()`, pages like Gitea (50 by default, or a smaller server cap), can ignore `page` to model a broken server, and records every write. A call budget makes a runaway loop fail the test instead of hanging it. Tests swap it in for `call()` and assert on the board and the writes.

`test_board_sync.py` also tests `tickets_named()` (which tickets a PR moves) and `main()` with an event file. `test_conformance.py` tests the `pr-ticket` check with an event file.

`test_check_entrypoint.py` builds three tiny images (executable, non-executable and no entrypoint) and runs `check-entrypoint.sh` on each.

`smoke-example.sh` is the smoke-test contract's example (`gitea-workflows`, Images); `test_smoke_contract.py` runs it against a working and a broken image; in CI it runs from a job container beside the Docker daemon, as `docker-image`'s step does. `conftest.py` holds `docker_works()`, which the integration tests skip on.

`test_push_image.py` pushes through `push-image.sh` to a throwaway `registry:2` in the daemon's own network namespace, and checks the host's tags afterwards.

`test_clean_run.py` checks `clean-run.sh` removes only what carries a run label, and that the example labels what it starts.

The tests sit flat in `ci/tests/`, one file per script, rather than in `unit/` and `integration/` folders: there are few, and each file holds one tier (its markers say which).

## Running locally

`ci/local-check.sh`, from the DEVKIT root, runs every check DEVKIT's CI runs, this suite included, in containers on your own Docker; run it before pushing, and CI runs them again on the PR. The command below runs this suite alone. The integration tests need the Docker socket, which gives the test container control of your Docker: run only this repo's tests this way. From the DEVKIT root (Git Bash on Windows needs `MSYS_NO_PATHCONV=1`):

```
docker run --rm -e PYTHONDONTWRITEBYTECODE=1 -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$PWD/ci:/w/ci" -w /w/ci/tests python:3.11-alpine sh -c \
  'apk add -q bash docker-cli && pip install -q -r requirements.txt && python -m pytest -q -p no:cacheprovider -m "unit or integration"'
```

## Bugs caught

- `test_push_image.py` failed on Docker Desktop: its registry was published on the laptop's loopback, which Desktop's daemon, inside its VM, cannot reach (`dial tcp [::1]` timed out, `127.0.0.1` was refused). The registry now runs with `--network host` on the daemon's loopback, which works on Linux and Desktop alike.

- `board_sync.py` read only the first 50 tickets of a column, so a ticket further down was added to the board again instead of moved. Fixed by reading every page.
- The first fix stopped at a page shorter than 50, which assumed Gitea's default page cap; a server with a lower cap brought the bug back, and a server ignoring `page` would loop until the job timed out. Now it stops at an empty page and gives up after 40 pages.
- An image whose `ENTRYPOINT` script was stored without the executable bit built, scanned and pushed cleanly, and failed only when a host started it (`permission denied`). `check-entrypoint.sh` now fails the image build instead; the non-executable test image reproduces it.
- The image job removed every tag it pushed from the runner's Docker, which is the host's, untagging the `:prep` images deployed stacks ran from. `push-image.sh` now puts each tag back on the image it had.
- A smoke script killed mid-run (by a step timeout, or a test stopping it) never ran its cleanup trap, leaving its container and network on the host; it happened twice while these tests were written. Everything a smoke script starts now carries a run label, and `clean-run.sh` removes it in a final step.
