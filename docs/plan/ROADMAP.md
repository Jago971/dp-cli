# Roadmap

**Scope:** Where DEVKIT is heading and where its work is tracked. Not history (see [../log/CHANGELOG.md](../log/CHANGELOG.md)) and not a task list: the tasks are Gitea tickets.
**Status:** current
**Last reviewed:** 2026-10-20

---

## Where we are heading

1. **Shared CI everywhere:** every repo's `ci.yml` calls DEVKIT's tests, security scan and conformance check, so CI is green and the same in every repo.
2. **Images by channel:** `prep` builds `:prep` images, a `vX.Y.Z` tag on `main` builds `:X.Y.Z`, and Hammond deploys by pulling them.
3. **Package publishing from shared actions:** PACKAGES' publish jobs call DEVKIT instead of copies.
4. **Standards still to write:** API hardening, logging and errors, dependency policy, performance KPIs.
5. **TLS for Gitea**, which retires the plain-HTTP registry setting.

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
