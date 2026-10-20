# Master copies

**Scope:** The fleet's approved dependency versions, which the `versions` job compares every repo against. Not the policy itself (the `gitea-workflows` skill, Dependency versions).
**Status:** current
**Last reviewed:** 2026-10-20

---

- `requirements.txt`: approved Python versions, `name==version`.
- `package.json`: approved npm versions, in `dependencies` and `devDependencies`.

Moved from WIKI `security/dependency_tracking/` on 2026-10-20 (last WIKI change `0b32dc9`). Revised the same day where osv-scanner flagged a master version (flask, requests, python-multipart, python-dotenv), react and react-dom moved to 18.3.1 as two repos run, and pytest, pytest-asyncio and pillow added at the versions the repos run (pillow then 13.0.0, after nine new advisories against 12.3.0). To change a version: review it in OWASP Dependency-Track, then open a DEVKIT PR; an Owner approves it.
