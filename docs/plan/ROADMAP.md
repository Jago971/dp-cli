# Roadmap

**Scope:** Where DEVKIT is heading and where its work is tracked. Not history (see [../log/CHANGELOG.md](../log/CHANGELOG.md)) and not a task list: the tasks are Gitea tickets.
**Status:** current
**Last reviewed:** 2026-10-26

---

## Where we are heading

1. **Local-first, containers only** (v0.7.0): dev on the laptop (Docker Desktop) → prep on Hammond → prod on an external server, not built yet. Nothing runs on a host outside containers; tests run locally before a push and CI re-runs them; servers pull images and never build; the CI runner stays with Gitea on Hammond for now, since there is no hardware to move it to (#70, parked).
2. **Deploy from images:** every repo's `ci.yml`, `board.yml` and image builds come from DEVKIT (2026-10-20). BDS and CURATOR prep stacks on Hammond pull `:prep` images; AHJ follows (AHJ#156).
3. **Dependency-Track:** the master copies reviewed there, and image SBOMs sent once a server URL is set.
4. **Standards still to write:** API hardening, logging and errors, performance KPIs; npm lockfiles (#32).
5. **TLS for Gitea** (#15, parked until the office can add a DNS record), which would retire the plain-HTTP registry setting on servers and laptops.

## Where the work is tracked

Tickets are on the [DEVKIT board](http://192.168.10.101:3393/Datumpin/DEVKIT/projects); plugin and CI findings from any repo land in its Triage.

| Milestone | Goal |
|---|---|
| v0.9.0 – Milestone release gate | The DoD column is the release gate, a release closes its milestone, and `dp` runs the release flow |

v0.5.0 (Shared CI and images), v0.6.0 (Guided flows), v0.7.0 (Local-first, containers only) and v0.8.0 (Lean flows: the `dp` CLI, `dp guide` and the token report) are released.

## Standing decisions

- **One repo for fleet tooling:** the plugin and the shared CI live here, not in WIKI (2026-10-20). WIKI keeps the business docs the skills point to.
- **Consumers follow `main`:** plugin installs and CI calls pin DEVKIT `main`; a change reaches them when it is released.
- **Channels are versions:** packages and images use the same rule; `prep` publishes pre-releases, `main` publishes finals.
- **Local first:** work is built and tested in containers on the laptop before it is pushed; CI is the second check, and staging and production hosts never run tests or builds (2026-10-21).
- **Milestone when started:** a Backlog ticket may have no milestone; it joins the earliest open milestone when work starts (#62, 2026-10-21).
- **Plain Docker Desktop on Windows, for now:** checkouts stay on the Windows drive, with LF line endings in every repo; moving them into WSL2 is the better long-term setup, tracked in #110 (#94, 2026-10-21).
- **A mechanical rule gets a check:** what `conformance` can check, it checks; the skills hold the judgement calls.
