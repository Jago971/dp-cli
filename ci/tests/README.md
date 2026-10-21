# ci/tests/

**Scope:** tests for the CI scripts in `ci/`, run by DEVKIT's `ci.yml` through the shared `python-tests` workflow (`working-directory: ci/tests`). 10 tests: 5 `unit`, 5 `integration` (need a Docker daemon; skipped without one).
**Status:** current
**Last reviewed:** 2026-10-21
**Governed by:** [docs/QUICKSTART.md](../../docs/QUICKSTART.md)

---

`fake_gitea.py` is an in-memory Gitea Board: it answers the calls `board_sync.py` makes through `call()`, pages like Gitea (50 by default, or a smaller server cap), can ignore `page` to model a broken server, and records every write. A call budget makes a runaway loop fail the test instead of hanging it. Tests swap it in for `call()` and assert on the board and the writes.

`test_check_entrypoint.py` builds three tiny images (executable, non-executable and no entrypoint) and runs `check-entrypoint.sh` on each.

`smoke-example.sh` is the smoke-test contract's example (`gitea-workflows`, Images); `test_smoke_contract.py` runs it against a working and a broken image; in CI it runs from a job container beside the Docker daemon, as `docker-image`'s step does. `conftest.py` holds `docker_works()`, which the integration tests skip on.

## Bugs caught

- `board_sync.py` read only the first 50 tickets of a column, so a ticket further down was added to the board again instead of moved. Fixed by reading every page.
- The first fix stopped at a page shorter than 50, which assumed Gitea's default page cap; a server with a lower cap brought the bug back, and a server ignoring `page` would loop until the job timed out. Now it stops at an empty page and gives up after 40 pages.
- An image whose `ENTRYPOINT` script was stored without the executable bit built, scanned and pushed cleanly, and failed only when a host started it (`permission denied`). `check-entrypoint.sh` now fails the image build instead; the non-executable test image reproduces it.
