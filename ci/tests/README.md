# ci/tests/

**Scope:** tests for the CI scripts in `ci/`, run by DEVKIT's `ci.yml` through the shared `python-tests` workflow (`working-directory: ci/tests`). 14 tests: 5 `unit`, 9 `integration` (need a Docker daemon; skipped without one).
**Status:** current
**Last reviewed:** 2026-10-21
**Governed by:** [docs/QUICKSTART.md](../../docs/QUICKSTART.md)

---

`fake_gitea.py` is an in-memory Gitea Board: it answers the calls `board_sync.py` makes through `call()`, pages like Gitea (50 by default, or a smaller server cap), can ignore `page` to model a broken server, and records every write. A call budget makes a runaway loop fail the test instead of hanging it. Tests swap it in for `call()` and assert on the board and the writes.

`test_check_entrypoint.py` builds three tiny images (executable, non-executable and no entrypoint) and runs `check-entrypoint.sh` on each.

`smoke-example.sh` is the smoke-test contract's example (`gitea-workflows`, Images); `test_smoke_contract.py` runs it against a working and a broken image; in CI it runs from a job container beside the Docker daemon, as `docker-image`'s step does. `conftest.py` holds `docker_works()`, which the integration tests skip on.

`test_push_image.py` pushes through `push-image.sh` to a throwaway `registry:2` and checks the host's tags afterwards.

`test_clean_run.py` checks `clean-run.sh` removes only what carries a run label, and that the example labels what it starts.

The tests sit flat in `ci/tests/`, one file per script, rather than in `unit/` and `integration/` folders: there are few, and each file holds one tier (its markers say which).

## Bugs caught

- `board_sync.py` read only the first 50 tickets of a column, so a ticket further down was added to the board again instead of moved. Fixed by reading every page.
- The first fix stopped at a page shorter than 50, which assumed Gitea's default page cap; a server with a lower cap brought the bug back, and a server ignoring `page` would loop until the job timed out. Now it stops at an empty page and gives up after 40 pages.
- An image whose `ENTRYPOINT` script was stored without the executable bit built, scanned and pushed cleanly, and failed only when a host started it (`permission denied`). `check-entrypoint.sh` now fails the image build instead; the non-executable test image reproduces it.
- The image job removed every tag it pushed from the runner's Docker, which is the host's, untagging the `:prep` images deployed stacks ran from. `push-image.sh` now puts each tag back on the image it had.
- A smoke script killed mid-run (by a step timeout, or a test stopping it) never ran its cleanup trap, leaving its container and network on the host; it happened twice while these tests were written. Everything a smoke script starts now carries a run label, and `clean-run.sh` removes it in a final step.
