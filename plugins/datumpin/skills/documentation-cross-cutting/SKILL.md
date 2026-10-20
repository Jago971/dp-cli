---
name: documentation-cross-cutting
description: Placing and writing documentation - where a fact belongs, setting up or auditing a docs tree, writing or editing any single markdown file (folder README, reference page, guide, plan doc).
---

# Documentation architecture and files

A repo's documentation is a layered system. Every fact has one home, decided by the placement tree below, and every doc below the root README opens with the same header.

## The layers

1. **Root `README.md`**: what the project is, plus a pointer to `docs/README.md`.
2. **`docs/QUICKSTART.md`**: the run/deploy/maintain tour (see `quickstart-guide`).
3. **`docs/README.md`**: the hand-maintained index. One line per current doc, grouped by domain, updated whenever a doc is added, moved or archived. The index lists current docs only.
4. **Folder READMEs**: every code folder with its own responsibility. It states what the folder owns, its boundary (what it deliberately does *not* do, and why a neighbouring folder that looks similar stays separate), and a `Governed by:` link to the cross-cutting doc that explains its shape. A status table (file, status, one line of design rationale) suits a folder of similar files (routers, services, test tiers).
5. **`docs/reference/<domain>/`**: cross-cutting, present-tense, no history. Architecture, data model, pipelines, ops and integration docs live here and point down via `Implemented in:` to every folder and file they describe.
6. **`docs/log/CHANGELOG.md`**: one global, append-only, dated log, because a split log loses cross-system prioritisation.
7. **`docs/plan/ROADMAP.md`** (plus standalone design plans): what is not built yet.
8. **`docs/_unverified/`**: content migrated from elsewhere and not yet checked against the code. Link it only from itself until it is verified and promoted.
9. **`docs/_archive/`**: confirmed-superseded content. Keep it frozen; promote by copying to `docs/reference/` with `Status: current`.

A decision-log doc (for example `docs/plan/MIGRATION_LOG.md`) records *why* a design choice was made. Use it on any rewrite or major refactor, alongside the CHANGELOG.

## The doc header

Every doc below the root README opens with:

```
# <Title>

**Scope:** <one sentence: what this covers, and what it deliberately does not>
**Status:** current | unverified | archived
**Last reviewed:** <YYYY-MM-DD>
**Governed by:** <link to the cross-cutting doc this is subordinate to, if any>
**Implemented in:** <links to folders/files this doc describes, if this IS a cross-cutting doc>

---
```

- Omit a field that does not apply.
- `Last reviewed` changes only when the content is re-checked.
- Link by heading text, since section numbers drift.
- Cross-references run both ways: local docs point up with `Governed by:`, cross-cutting docs point down with `Implemented in:`.

## Placement tree

Ask in order:

1. Did it just ship or happen? `docs/log/CHANGELOG.md`.
2. Is it a plan, not built yet? `docs/plan/ROADMAP.md`.
3. Does understanding it need more than one folder? `docs/reference/<domain>/`. Otherwise the single folder's `README.md`.
4. Unsure it is still accurate? `docs/_unverified/`, and say so.
5. Confirmed dead or replaced? `docs/_archive/`, with a pointer left where it used to be referenced.

## Writing a single file

- Present tense for what is true now. Past tense lives in the CHANGELOG and decision log.
- Record a design decision's reason and its rejected alternatives in a present-tense line (`Rejected: X, because Y`). The incident story belongs in the CHANGELOG.
- Describe intent, boundaries and the why, and link to the code for the what.
- Use a comparison table for parallel variants (dev against prod, tier A against tier B): one column per dimension, one row per variant.
- Docs stand alone months later: name no ticket, PR or meeting, and link to another doc where the content already lives.

## Diagrams

Draw a flow, a lifecycle or an architecture when a picture says it faster than a paragraph; otherwise write prose.

- Use a Mermaid block (` ```mermaid `) in the markdown file. Gitea renders it, and it diffs like text. No image files for what Mermaid can draw.
- One idea per diagram, about 15 nodes at most. Split a bigger one.
- Prose beside it says what the reader should take from it; the diagram never replaces the text.
- Label nodes with the names used in the code and docs.
- Check it renders in Gitea before merging.

## Auditing an existing docs tree

Check each of these and fix links to the exact on-disk name, case included (Linux and Gitea links are case-sensitive):

- The root README and index link only to paths that exist.
- Every top-level folder is reachable from `docs/README.md`.
- Link targets contain no spaces or special characters.
- Two versions of an asset (two dated diagrams) sit beside a doc saying which is current.
- Every README is finished, or marked as a stub.

## Done when

- **Placing a fact:** it sits in exactly one file, and that file is listed in `docs/README.md` (unless under `_unverified/` or `_archive/`).
- **Writing a file:** the header is complete, every link resolves case-exactly, each `Implemented in:` target has a matching `Governed by:` back-link, and `docs/README.md` has the entry.
- **Setting up:** layers 1 to 5 exist and every folder with its own responsibility has a README.
- **Auditing:** every link and every top-level folder has been checked.
