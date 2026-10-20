# Datumpin Claude Skills

Skills that make Claude Code behave consistently across Datumpin projects: same
documentation architecture, same comment/docstring shape, same testing
taxonomy, same secret handling, same Docker/Gitea conventions.

These are distilled from what already works well in `AHJV2`, `BDS`, `CURATOR`
and `PACKAGES`. Where one repo has set a convention, every repo follows it and
the skill records it; where the repos were inconsistent or had a gap (no linter
config, no coverage tooling), the skill sets a real standard rather than
copying the gap. The skills are the single source of truth for the cross-repo
conventions: instance folders, env files, seeding, settings, ports, networks,
generated compose files, and the shared "Engineering principles" block (see
`claude-md-authoring`).

This folder is the skill set of the `datumpin` Claude Code plugin (see
[../README.md](../README.md)). A repo with the plugin installed gets every skill
here, kept current by the plugin version.

**Standing duty, until every repo has the plugin:** any change to a skill is
mirrored byte-identically into every repo that still carries a root `skills/`
copy and lists it in its `CLAUDE.md`, in the same change. The duty ends for a
repo once it installs the plugin and drops its copy.

## Skills in this set

| Skill | Use when |
|---|---|
| [documentation-cross-cutting](documentation-cross-cutting/SKILL.md) | Placing or writing documentation: docs architecture, where a fact belongs, writing any single markdown file (folder README, reference doc, guide) |
| [quickstart-guide](quickstart-guide/SKILL.md) | Creating or updating a repo's `docs/QUICKSTART.md` — the short, human-readable tour: run it, deploy it, maintain it, where to go deeper |
| [code-comments-and-docstrings](code-comments-and-docstrings/SKILL.md) | Writing or editing comments, docstrings or `#region` fold markers in any source file |
| [testing-conventions](testing-conventions/SKILL.md) | Writing tests, test READMEs, or setting up a test suite |
| [api-documentation](api-documentation/SKILL.md) | Documenting or building HTTP APIs (FastAPI/Express/etc.) |
| [secrets-handling](secrets-handling/SKILL.md) | Adding config, env vars, or credentials anywhere in a project |
| [docker-compose-conventions](docker-compose-conventions/SKILL.md) | Writing/editing Dockerfiles or docker-compose files |
| [gitea-workflows](gitea-workflows/SKILL.md) | Writing or editing `.gitea/workflows/` CI pipelines |
| [claude-md-authoring](claude-md-authoring/SKILL.md) | Writing or updating a repo's own `CLAUDE.md` |
| [fastapi-service-architecture](fastapi-service-architecture/SKILL.md) | Scaffolding or extending a FastAPI service — routers/services/database layering, typed settings, migrations/seeding, config-driven multi-instance deployment |
| [config-led-deployment](config-led-deployment/SKILL.md) | Standing up a new product instance: the instance folder, root-level env files, the two seeding patterns, ports, networks, generated compose files |
| [roles-and-permissions](roles-and-permissions/SKILL.md) | Adding user accounts, login/sessions, or role/permission checks to any service — identity vs. per-app authorization, dependency-injected auth |
| [alembic-migrations](alembic-migrations/SKILL.md) | Setting up or adding a migration to a FastAPI/SQLAlchemy service — env.py wiring, SQLite batch mode, container-only commands |
| [react-frontend-architecture](react-frontend-architecture/SKILL.md) | Building or extending a React frontend — CSS Modules layout, config-driven generic components, plain fetch-function API modules, the fetch-hook/adapter/vendor-wrapper pattern |
| [writing-for-agents](writing-for-agents/SKILL.md) | Writing or editing a skill, CLAUDE.md or any doc an agent reads (credited, see [CREDITS.md](CREDITS.md)) |
| [grilling](grilling/SKILL.md) | Stress-testing a plan or decision by interview until every branch is resolved (credited) |
| [grill-me](grill-me/SKILL.md) | User-invoked entry to `grilling` (credited) |
| [domain-modeling](domain-modeling/SKILL.md) | Building a `GLOSSARY.md` and recording hard-to-reverse decisions in the decision log (credited, adapted) |
| [tdd](tdd/SKILL.md) | Building features or fixes test-first, red before green, at agreed seams (credited, adapted) |
| [diagnosing-bugs](diagnosing-bugs/SKILL.md) | Hard bugs or regressions: build a tight red feedback loop first (credited, adapted) |
| [handoff](handoff/SKILL.md) | User-invoked: compact a session into a document another agent can continue from (credited, adapted) |
| [retro](retro/SKILL.md) | User-invoked: review a session and suggest improvements to the agent's environment (credited) |
| [definition-of-done](definition-of-done/SKILL.md) | Finishing a change: the checklist a change passes before it is called done or opened as a PR, and how it relates to the promotion worksheet |
| [change-review](change-review/SKILL.md) | Reviewing a diff on two separate axes (Standards, Spec) with parallel subagents and human adjudication |
| [skills-router](skills-router/SKILL.md) | User-invoked: which skill fits my situation, and the usual order of work |
| [board](board/SKILL.md) | `/datumpin:board`: sync the repo's Gitea tickets, show the kanban, suggest the next ticket |
| [shape](shape/SKILL.md) | `/datumpin:shape`: turn an idea or vague ticket into scoped Gitea tickets, or a milestone |
| [align](align/SKILL.md) | `/datumpin:align`: find drift between code, tickets and plans, then fix it (Reset when a repo joins, Review later) |
| [gitea](gitea/SKILL.md) | Reading or writing Gitea through `tea`: commands, write rules, labels, milestones |
| [formats](formats/SKILL.md) | The fixed output shapes of workflow steps: log lines, board view, ticket body |

## How to use these in a new project

1. Install the plugin in the project (see [../README.md](../README.md)).
2. Write a short root `CLAUDE.md` using the `claude-md-authoring` skill —
   it should mostly just point at these skills and at the project's own
   `docs/_meta/` governing docs, not restate their content.
3. Run `documentation-cross-cutting` once at project start to scaffold the
   docs layout, then let the per-topic skills apply themselves as work happens.

## Credits

Eight skills come from Matt Pocock's MIT-licensed `mattpocock/skills`. See [CREDITS.md](CREDITS.md) for which ones, what was changed, and his licence.

## Source material

Patterns here are drawn from `AHJV2` (`docs/_meta/HOW_TO_DOCUMENT.md`,
`docs/_meta/COMMENTING_CONVENTIONS.md`, `docs/plan/testing-strategy.md`,
`docs/reference/ops/docker.md`) and `BDS` (same `docs/_meta/` pair, plus its
BuildKit-secrets Dockerfile pattern and `docs/plan/MIGRATION_LOG.md`
decision-log habit). Both repos are internal Datumpin projects — see them
directly for full worked examples.
