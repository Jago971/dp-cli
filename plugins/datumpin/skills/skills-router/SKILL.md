---
name: skills-router
description: Which Datumpin skill fits my situation, and the usual order of work.
disable-model-invocation: true
---

# Skills router

Names the skill to reach for and the order a change usually moves through. It points only. Name the skill to the agent, or let the agent reach the model-invoked ones itself.

## The flow of a change

| Step | Situation | Skill |
|---|---|---|
| 0 | Starting a session, or choosing what to work on | `board` |
| 0 | An idea or vague ticket needs turning into tickets | `shape` |
| 0 | The backlog or roadmap is out of date, a repo joins the workflow, or a milestone closed | `align` |
| 1 | The plan is vague, or you want it stress-tested | `grill-me` (user-invoked), which runs `grilling` |
| 2 | Terms are fuzzy or overloaded | `domain-modeling` |
| 3 | Writing the plan down | `documentation-cross-cutting` (plans go in `docs/plan/`) |
| 4 | Building | `tdd`, with `testing-conventions`, and the area skill below |
| 5 | Something is broken | `diagnosing-bugs` |
| 6 | Reviewing the diff | `change-review` |
| 7 | Is it finished | `definition-of-done` |
| 8 | CI, branches, PRs | `gitea-workflows` |
| 9 | A skill changed | Bump the plugin version (plugin README, Releasing a change); `writing-for-agents` |
| 10 | End of a session | `handoff`, then `retro` (both user-invoked) |

## By area

| Working on | Skill |
|---|---|
| FastAPI service layout, settings, instances, DB patterns | `fastapi-service-architecture` |
| Migrations | `alembic-migrations` |
| Accounts, sessions, roles | `roles-and-permissions` |
| React frontend | `react-frontend-architecture` |
| Instance folders, env files, ports, networks, seeding | `config-led-deployment` |
| Dockerfiles and compose | `docker-compose-conventions` |
| Secrets and credentials | `secrets-handling` |
| Comments, docstrings, region markers | `code-comments-and-docstrings` |
| Docs placement and single files | `documentation-cross-cutting` |
| `docs/QUICKSTART.md` | `quickstart-guide` |
| Endpoint docs | `api-documentation` |
| Writing a skill or a CLAUDE.md | `writing-for-agents`, `claude-md-authoring` |
| Gitea tickets, labels, milestones | `gitea` |
| Output shape of a workflow step | `formats` |

## Keeping this map true

When a skill is added, renamed, removed or changes what it covers, update this file in the same change. A router that names a stale skill sends people to the wrong place.

## Done when

- Every skill folder in `skills/` appears in a table above, or is a user-invoked helper named in the flow.
- Every skill named above exists in `skills/`.
