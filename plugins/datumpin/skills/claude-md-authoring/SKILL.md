---
name: claude-md-authoring
description: Writing or updating a repo's CLAUDE.md - the Datumpin Engineering-principles block, the pointer to the datumpin plugin, subfolder CLAUDE.md. General agent-document writing belongs to writing-for-agents.
---

# Writing a repo's CLAUDE.md

General rules (context pointers, single source of truth, pruning) live in `writing-for-agents`. A CLAUDE.md routes to the governing skill or doc for each kind of task and holds stable pointers and overrides: response style, git/PR overrides, dev-environment quirks, where to start (`docs/README.md`). Changing state (sprint focus, in-flight branches) lives in the ROADMAP or CHANGELOG. BDS's `CLAUDE.md` is the worked example.

## The shared Engineering-principles block

Every Datumpin repo's `CLAUDE.md` carries the block in the same shape: the lead line, then one bullet per principle as `**Name:** one or two sentences.`

> Every change should be **secure, modular, reusable, conventional, simple, readable, maintainable, follow established patterns**.

The bullets cover those eight, then **Config-led**, **No fallback identity**, **No dual-version code at runtime** and **Parallel fixes** (while old and new builds run in parallel). Repo-specific nouns vary, and the wording shape stays fixed.

> **Follow established patterns:** when one repo has set a convention, every repo follows it, and the skill records it. Deviate only deliberately, with the reason documented. A new pattern goes into the shared skill in the same change.

**Config-led** says one build point per instance. Assets, seeds, branding and keys are supplied up front in `instances/<name>/`, and env files stay at the repo root (`.env.<app>-<instance>[.dev]`).

## Skills come from the plugin

A repo in the workflow has the `datumpin` plugin installed (see the plugin README in DEVKIT) and keeps no copy of the shared skills. Its `CLAUDE.md` lists no skills; it carries one short section instead:

> **Skills and workflow.** The shared Datumpin skills and the workflow flows come from the `datumpin` plugin (DEVKIT `plugins/datumpin/`). They load by their trigger words; `/datumpin:skills-router` maps them. Tickets, milestones and the board live in Gitea: `/datumpin:board`, `/datumpin:shape`, `/datumpin:align`.

A skill only this repo needs lives in the repo's `.claude/skills/`. Keep the principles block in step across repos in the same change.

## Section order

Every repo's `CLAUDE.md` opens with the same four sections, in this order, then its own:

1. `## Response style`
2. `## Engineering principles`
3. `## Git commits and PRs`
4. `## Skills and workflow`

Repo-specific sections (what the repo is, its origin, its conventions, the dev environment) follow. The eight core principles always appear; **Config-led**, **No fallback identity**, **No dual-version code at runtime** and **Parallel fixes** appear where they apply, under those exact names. The shared `conformance` CI job checks the four sections, their order and the eight core principles.

## A second CLAUDE.md in a subfolder

When one subfolder has its own process (a rewrite plan with its own method), a scoped `CLAUDE.md` there carries that process and the root stays general. BDS's `docs/plan/CLAUDE.md` is the worked example.

## Done when

- The CLAUDE.md is under about 100 lines and holds no convention text a skill already holds.
- The principles block matches the canonical wording above.
- It carries the Skills and workflow section, and no root `skills/` folder remains.
