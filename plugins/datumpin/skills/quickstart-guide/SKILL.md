---
name: quickstart-guide
description: Writing docs/QUICKSTART.md - the short tour for running, deploying and maintaining a repo. Use when creating it or when a run or deploy command changes.
---

# Quickstart guide

One file per repo, `docs/QUICKSTART.md`, first in `docs/README.md`'s index. It takes a reader from "I just opened this repo" to "I can run it, deploy it, and know where to look next", in under 100 lines. It opens with the standard header from `documentation-cross-cutting` (`Governed by: docs/README.md`).

## Sections, in this order

1. **What this is**: 2-3 plain sentences, acronyms expanded on first use.
2. **Quick-start**: copy-pasteable commands to clone, create env files from the `.example` files, and bring it up in containers.
3. **Map of the pieces**: one line per service or component (name, purpose, where it lives).
4. **How to deploy**: the real command, or a one-line pointer to the doc that has it.
5. **Common maintenance tasks**: migrations, adding a seed, restarting a service. One line each.
6. **Where to go deeper**: a table of topic against the governing doc (`docs/reference/...`, a folder README, `docs/plan/ROADMAP.md`). Everything past a one-liner lives behind this table.
7. **When stuck**: `CLAUDE.md`, the skills directory, the roadmap.

## Rules

- A paragraph's worth of content goes in a `docs/reference/` doc, with a link here.
- Each section stays at about ten lines or fewer.
- State what to do now, in the present tense. History and plans live in the CHANGELOG and ROADMAP.
- Update it when a quick-start command, deploy step or component changes. Mark an unknown step `TODO`.

## Done when

- The seven sections exist in order.
- Every command in Quick-start was run from a clean checkout and exited 0.
- Every "deeper" row links to an existing file.
- The file is first in `docs/README.md` and under 100 lines.
