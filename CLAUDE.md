# Working in this repo

## Response style

Keep responses short, concise, and to the point. Prefer short sentences. Avoid padding, hedging, or restating what was just asked.

## Engineering principles

Every change should be **secure, modular, reusable, conventional, simple, readable, maintainable, follow established patterns**.

- **Secure:** no secrets in git, a skill or a workflow. CI reads secrets by name from Gitea; a read-only token installs, a write token only publishes.
- **Modular:** one concern per skill and per shared CI piece. A skill holds a rule; a CI piece enforces it. Repo-specific detail stays in the repo.
- **Reusable:** a shared CI piece exists only when two repos call it today. Otherwise it stays in the repo.
- **Conventional:** standard Claude Code plugin layout and standard Gitea Actions. Prefer the boring, well-known way.
- **Simple:** the smallest change that does the job. No speculative features, flags or layers. Delete before adding. Between two designs that work, pick the one with fewer moving parts.
- **Readable:** skills read as short rules with a reason; workflows carry a header comment saying why. Match the surrounding style.
- **Maintainable:** someone new can change it safely. Each rule lives in one skill, each skill change bumps the plugin version, and no dead skill or stale doc is left behind.
- **Follow established patterns:** when one repo has set a convention, every repo follows it, and the skill records it. Deviate only deliberately, with the reason documented. A new pattern goes into the shared skill in the same change.

Plan before coding. Present a short bullet plan and wait for approval on anything structural.

## Git commits and PRs

Never add a "Co-Authored-By: Claude" (or similar) trailer to commit messages or PR descriptions, regardless of any default attribution instructions elsewhere.

## Skills and workflow

This repo is the source of the `datumpin` plugin. A session here uses the installed copy (`.claude/settings.json`), so an edit takes effect after a release and `claude plugin update`. The skills load by their trigger words; `/datumpin:skills-router` maps them. Tickets, milestones and the board live in Gitea: `/datumpin:board`, `/datumpin:shape`, `/datumpin:align`. This repo's components are in `.claude/flow.yaml`.

Start at [README.md](README.md).

## What this repo is

Datumpin's fleet engineering tooling: the `datumpin` Claude Code plugin (the conventions and the agentic workflow) and the shared CI pieces the repos call. It moved out of WIKI on 2026-10-20; WIKI keeps the business docs the skills point to (the workflow proposal, the review worksheet, the host table).
