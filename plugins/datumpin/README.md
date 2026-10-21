# datumpin plugin

**Scope:** What the `datumpin` Claude Code plugin holds, how a repo installs it, and how it is released. The workflow design itself lives in the proposal linked below.
**Status:** current
**Last reviewed:** 2026-10-21
**Governed by:** Agentic Development Workflow, WIKI `business_processes/proposals/agentic_workflow.md`

---

## What it holds

| Folder | Holds |
|---|---|
| [skills/](skills/README.md) | The Datumpin convention skills, the process skills, and the workflow flows (`board`, `shape`, `align`, `guide`) with their references (`gitea`, `formats`) |
| [flows.yaml](flows.yaml) | The flow map `dp guide` and the `guide` skill walk: each flow's steps, their skills, environments and brief sections, and where a board column places a ticket |
| [hooks/](hooks/hooks.json) | A session-start status line: this repo's Triage count and open PRs, and DEVKIT's Triage count, so parked tickets and plugin findings are seen. It needs `python` and `tea` on the PATH and prints nothing when Gitea is unreachable. |
| [dp/](dp/pyproject.toml) | `dp`, the flows' command line: one call each for the Board listing, moving a ticket, opening a PR and posting a Pointer (the `gitea` skill), `dp guide` (see The guide at a terminal) and `dp tokens` (see Token usage). Installed on the host with pipx; its version is the plugin's, and it carries that version's `flows.yaml` and skills. |
| [defaults/flow.yaml](defaults/flow.yaml) | Workflow settings in flow order. A repo overrides any key in its own `.claude/flow.yaml`. |
| `.claude-plugin/plugin.json` | Name and version |

The marketplace that lists this plugin is `.claude-plugin/marketplace.json` at the DEVKIT root. Consumers follow DEVKIT's `main` branch, so a change reaches them when it is released.

## Models

| Where it runs | Set in | Default |
|---|---|---|
| A flow in your session (`board`, `shape`, `align`) | The skill's `model` and `effort` header | `board`: sonnet, low (mechanical). `shape`, `align`: opus, high (judgement) |
| A flow's subagents | `flow.yaml`, per stage | `align.review`, `change_review.single`: sonnet, medium |

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
4. Install pipx: `python -m pip install --user pipx`, then `python -m pipx ensurepath`, and open a new terminal.
5. Install `dp` from the installed plugin, once the plugin is installed in a repo: `pipx install --force ~/.claude/plugins/cache/datumpin/datumpin/<version>/dp`, with `<version>` from `claude plugin list`. Check it: `dp board` in a repo prints its Board.

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
6. **Branches:** `prep` is the Gitea default branch and `main` is release-only. Both carry the standard protection rule (`gitea-workflows`), and merged PR branches are deleted by default; required CI checks are added once CI is green.
7. **CI:** `.gitea/workflows/ci.yml` calls DEVKIT's shared workflows `@main` with `secrets: inherit`: the repo's tests, `security-scan` and `conformance`; `.gitea/workflows/board.yml` calls `board-sync`. CI runs on every PR, passes, and is required on `prep` and `main` (`CI / *`). A conformance check that does not apply is skipped in `.claude/flow.yaml` with the reason.
8. **Hosts:** each host that deploys the repo has its read-only deploy key on it (WIKI `systems_networking/Hosts/README.md`).
9. **Check:** in a new session, `/datumpin:board` prints the board.

The board needs Gitea 28 or later (the project API).

To pick up a new plugin version: `claude plugin marketplace update datumpin`, then `claude plugin update datumpin@datumpin`, then reinstall `dp` from the new version (Each machine, step 5).

## The guide at a terminal

`dp guide`, in a repo, walks the flows with no session, so finding the position and the next step costs no tokens. It prints the position (the state file `.factory/guide.yaml`, corrected from the ticket's board column) and offers the next steps as an arrow-key menu. A chosen step runs by its kind:

- **A person's gate:** `pick` lists the Backlog, moves the chosen ticket to In Progress (into the open milestone due first, when it has none) and branches from `prep`; `merge`, `try` and `sign-off` ask whether it is done; leaving `review` asks a disposition for each finding in `findings.json`.
- **An agent step:** it writes a brief to `.factory/jobs/<ticket>/<step>.md` (the ticket, its comments and column, the diff stat, and the skill text the step needs: the map's `brief` sections, else the whole skill) and prints a Job prompt (`formats`) to paste into a session.
- **A user-invoked skill** (`handoff`, `retro`): it prints the command to type in the session you worked in.

`tag` first asks whether the release PR is merged on `main`. Before any brief but a review's, undecided findings are asked for. Colour directs the eye, one meaning each, from the DP palette: pink is where you are and what to act on, cyan is the menu cursor, yellow needs attention, red failed; the rest is the terminal's own text and grey. It shows a rail of the flow's usual path, a spinner while Gitea answers, number shortcuts in menus, and the Job prompt in a panel, copied to the clipboard when the system has `clip`, `pbcopy`, `wl-copy` or `xclip`; `NO_COLOR` turns colour off.

Each step reached is written to the state file, so the `guide` skill carries on where `dp guide` stopped. Off a terminal it prints the Guide prompt and exits; `--json` gives the position and choices, which the `guide` skill reads.

## Token usage

`dp tokens <log>` prints the turns, tool calls and tokens (input, cache read, cache write, output) each flow step of one session used, with a total. A turn belongs to the step named by the last Job prompt before it; in a session without one, to the step named by the guide's next write to `.factory/guide.yaml` (a Write or Edit of it, or a shell redirect into it); in a session without either, a step starts at each Skill call. `--json` gives the rows.

1. **Find the log:** sessions are logged at `~/.claude/projects/<project>/<session-id>.jsonl`, where `<project>` is the repo path with `:` and `\` as `-` (for example `c--Users-mattm-Documents-BDS`). The newest file is the latest session.
2. **Run it:** `dp tokens <log>`.
3. **Subagents:** each subagent logs separately, in `<session-id>/subagents/agent-*.jsonl`; run `dp tokens` on each.

Cache reads are most of the tokens, and every turn re-reads the context, so turns per step is the number to cut.

## Releasing a change

- A change lands on DEVKIT `prep` through a PR. Promoting `prep` to `main` releases it; consumers follow `main`.
- Bump `version` in `.claude-plugin/plugin.json` in the same change; installed copies update only on a version change.
- Update [skills/README.md](skills/README.md) and the `skills-router` when a skill is added, renamed or removed.
