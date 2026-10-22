# Git shapes

Commit messages and branch names. Parent: [SKILL.md](SKILL.md).

## Commit

`<area>: <what changed>`

- `<area>` is the folder, service or topic in lower case (`docs`, `api`, `processor`, `ci`, `gitignore`); the subject is 72 characters or fewer.
- An optional body gives the why in short lines, and `Refs #N` when there is a ticket (`See #N` for one it only relates to).
- No AI attribution trailer.

## Branch

`<type>/<issue>-<slug>`, e.g. `feat/44-headstart-ap-blac-chpg`. `<type>` is `feat`, `fix`, `chore` or `docs`. Without a ticket: `<type>/<slug>`.
