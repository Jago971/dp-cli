# ci/tests/

**Scope:** tests for the CI scripts in `ci/`, run by DEVKIT's `ci.yml` through the shared `python-tests` workflow (`working-directory: ci/tests`). 5 tests, all `unit`.
**Status:** current
**Last reviewed:** 2026-10-21
**Governed by:** [docs/QUICKSTART.md](../../docs/QUICKSTART.md)

---

`fake_gitea.py` is an in-memory Gitea Board: it answers the calls `board_sync.py` makes through `call()`, pages like Gitea (50 by default, or a smaller server cap), can ignore `page` to model a broken server, and records every write. A call budget makes a runaway loop fail the test instead of hanging it. Tests swap it in for `call()` and assert on the board and the writes.

## Bugs caught

- `board_sync.py` read only the first 50 tickets of a column, so a ticket further down was added to the board again instead of moved. Fixed by reading every page.
- The first fix stopped at a page shorter than 50, which assumed Gitea's default page cap; a server with a lower cap brought the bug back, and a server ignoring `page` would loop until the job timed out. Now it stops at an empty page and gives up after 40 pages.
