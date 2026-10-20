# datumpin plugin

**Scope:** What the `datumpin` Claude Code plugin holds, how a repo installs it, and how it is released. The workflow design itself lives in the proposal linked below.
**Status:** current
**Last reviewed:** 2026-10-20
**Governed by:** [Agentic Development Workflow](../../business_processes/proposals/agentic_workflow.md)

---

## What it holds

| Folder | Holds |
|---|---|
| [skills/](skills/README.md) | The Datumpin convention skills, the process skills, and the workflow flows (`board`, `shape`, `align`) with their references (`gitea`, `formats`) |
| [hooks/](hooks/hooks.json) | A session-start status line: this repo's Triage count and open PRs, and DEVKIT's Triage count, so parked tickets and plugin findings are seen. It needs `python` and `tea` on the PATH and prints nothing when Gitea is unreachable. |
| [defaults/flow.yaml](defaults/flow.yaml) | Workflow settings in flow order. A repo overrides any key in its own `.claude/flow.yaml`. |
| `.claude-plugin/plugin.json` | Name and version |

The marketplace that lists this plugin is `.claude-plugin/marketplace.json` at the DEVKIT root. Consumers follow DEVKIT's `main` branch, so a change reaches them when it is released.

## Models

| Where it runs | Set in | Default |
|---|---|---|
| A flow in your session (`board`, `shape`, `align`) | The skill's `model` and `effort` header | `board`: sonnet, low (mechanical). `shape`, `align`: opus, high (judgement) |
| A flow's subagents | `flow.yaml`, per stage | `align.review`: sonnet, medium |

A skill header applies only to the turn the skill starts in; your next message runs on the session model. `shape` interviews over many turns, so switch the session to Opus (`/model opus`) before shaping. Header defaults are plugin-wide; a repo cannot override them.

## Each machine, once

1. Add a `gitea` SSH alias to `~/.ssh/config`. The plugin CLI accepts only the `git@host:path` URL form, which cannot carry Gitea's SSH port:

   ```
   Host gitea
       HostName 192.168.10.101
       Port 2222
       User git
   ```

2. Check it: `git ls-remote git@gitea:Datumpin/DEVKIT.git main` prints a commit.
3. Install `tea` and add two logins: the engineer's own, and `squire` (the agent's).

## Bringing a repo into the workflow

Run in order. A check that cannot pass yet becomes a ticket on the repo's board; `align` drafts those tickets in Reset mode.

1. **Gitea access:** add the repo to the Gitea team `Agents`, so the bot account can work in it.
2. **Install:** from the repo root, register the marketplace and install. The VS Code extension does not install from settings alone; use its bundled `claude.exe` under `~/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/`:

   ```
   claude plugin marketplace add git@gitea:Datumpin/DEVKIT.git#main --scope project
   claude plugin install datumpin@datumpin --scope project
   ```

   This writes `.claude/settings.json`; commit it. On another machine, with the file already committed, only the `install` line is needed.
3. **Cache:** add `.factory/` to the repo's `.gitignore`.
4. **Reset:** run `/datumpin:align` in a new session. Reset mode creates the `Board` project and the component labels, rebuilds the milestones and tickets from the docs, closes the old tickets and projects, and opens a PR with the roadmap rewrite and the repo's `components` in `.claude/flow.yaml`.
5. **Skills copy:** delete the root `skills/` folder and replace the skill list in `CLAUDE.md` with the Skills and workflow section (see `claude-md-authoring`).
6. **Branches:** `prep` is the Gitea default branch and `main` is release-only. Both carry the standard protection rule (`gitea-workflows`); required CI checks are added once CI is green.
7. **CI:** `.gitea/workflows/ci.yml` calls DEVKIT's shared workflows `@main` with `secrets: inherit`: the repo's tests, `security-scan` and `conformance`. It runs on every PR and passes. A conformance check that does not apply is skipped in `.claude/flow.yaml` with the reason.
8. **Hosts:** each host that deploys the repo has its read-only deploy key on it (WIKI `systems_networking/Hosts/README.md`).
9. **Check:** in a new session, `/datumpin:board` prints the board.

The board needs Gitea 28 or later (the project API).

To pick up a new plugin version: `claude plugin marketplace update datumpin`, then `claude plugin update datumpin@datumpin`.

## Releasing a change

- A change lands on DEVKIT `prep` through a PR. Promoting `prep` to `main` releases it; consumers follow `main`.
- Bump `version` in `.claude-plugin/plugin.json` in the same change; installed copies update only on a version change.
- Update [skills/README.md](skills/README.md) and the `skills-router` when a skill is added, renamed or removed.
