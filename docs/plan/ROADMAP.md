# Roadmap

**Scope:** Where DEVKIT is heading and where its work is tracked. Not history (see [../log/CHANGELOG.md](../log/CHANGELOG.md)) and not a task list: the tasks are Gitea tickets.
**Status:** current
**Last reviewed:** 2026-10-20

---

## Where we are heading

1. **Deploy from images:** every repo's `ci.yml`, `board.yml` and image builds already come from DEVKIT (2026-10-20); Hammond still builds from source and moves to `docker compose pull` of the `:prep` images (BDS, AHJ, CURATOR tickets).
2. **Dependency-Track:** the master copies reviewed there, and image SBOMs sent once a server URL is set.
3. **Standards still to write:** API hardening, logging and errors, performance KPIs; npm lockfiles (#32).
4. **TLS for Gitea**, which retires the plain-HTTP registry setting.

## Where the work is tracked

Tickets are on the [DEVKIT board](http://192.168.10.101:3393/Datumpin/DEVKIT/projects); plugin and CI findings from any repo land in its Triage.

| Milestone | Goal |
|---|---|
| v0.5.0 – Shared CI and images | Every repo runs its tests, scans and image builds from DEVKIT's shared CI, and images reach the registry by channel |

## Standing decisions

- **One repo for fleet tooling:** the plugin and the shared CI live here, not in WIKI (2026-10-20). WIKI keeps the business docs the skills point to.
- **Consumers follow `main`:** plugin installs and CI calls pin DEVKIT `main`; a change reaches them when it is released.
- **Channels are versions:** packages and images use the same rule; `prep` publishes pre-releases, `main` publishes finals.
- **A mechanical rule gets a check:** what `conformance` can check, it checks; the skills hold the judgement calls.
