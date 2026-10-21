# ci/tests/

**Scope:** tests for the CI scripts in `ci/`, run by DEVKIT's `ci.yml` (`python -m pytest -q ci/tests`).
**Status:** current
**Last reviewed:** 2026-10-21
**Governed by:** [docs/QUICKSTART.md](../../docs/QUICKSTART.md)

---

`fake_gitea.py` is an in-memory Gitea Board: it answers the calls `board_sync.py` makes through `call()`, pages at 50 like Gitea, and records every write. Tests swap it in for `call()` and assert on the board and the writes.

## Bugs caught

- `board_sync.py` read only the first 50 tickets of a column, so a ticket further down was added to the board again instead of moved. Fixed by reading every page.
