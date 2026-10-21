# DEVKIT

Datumpin's fleet engineering tooling, shared by BDS, AHJ, CURATOR and PACKAGES.

| Folder | Holds |
|---|---|
| [plugins/datumpin/](plugins/datumpin/README.md) | The `datumpin` Claude Code plugin: the convention skills and the agentic workflow (`board`, `shape`, `align`) |
| [.claude-plugin/marketplace.json](.claude-plugin/marketplace.json) | The marketplace that lists the plugin |
| [docs/](docs/README.md) | Quickstart, roadmap, changelog |
| [ci/](ci/tests/README.md) | The scripts the shared workflows run (conformance, versions, board sync, image push), the approved versions in `ci/master/`, and their tests |
| [docs/runner.md](docs/runner.md) | The Actions runner on Hammond: start, upgrade, roll back, and the Docker settings CI needs |

The shared CI workflows the repos call are in `.gitea/workflows/`: tests, the security scan (with the version lock against `ci/master/`), conformance, board sync, image builds and package publishing. New here: [docs/QUICKSTART.md](docs/QUICKSTART.md).

## Branches and releases

`prep` is the default branch; every change lands there through a PR. Promoting `prep` to `main` is a release. Consumers follow `main`: a repo's `.claude/settings.json` pins the marketplace to it.

```
claude plugin marketplace add git@gitea:Datumpin/DEVKIT.git#main --scope project
claude plugin install datumpin@datumpin --scope project
```

Installing on a new machine and bringing a repo into the workflow: [plugins/datumpin/README.md](plugins/datumpin/README.md).

## History

The plugin moved here from WIKI on 2026-10-20, imported from WIKI `main` at `d91ab23`. Its earlier history is in WIKI. The business docs the skills point to (the workflow proposal, the review worksheet, the host table) stay in WIKI.
