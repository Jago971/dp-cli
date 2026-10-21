# Rolling out onto a live server

For a restructure that moves data (databases, clean data, logs), or a deployment running beside an older live one. Parent: [SKILL.md](SKILL.md).

A rollout doc under `docs/plan/` is written before anything runs. It states:

- **Backup** of everything that moves, taken first.
- **Move, not re-run.** Existing files move into the new layout, and ingest does not regenerate them.
- **Verification** after the move: counts, a query per database, one real scheduled tick.
- **Rollback.** The old layout returns by moving the files back, with the exact commands written down.

The older live deployment stays untouched until the new one is verified.

## Running beside an older live deployment

A server deployment that runs next to an older live one adds +1000 to each host port through the `*_HOST_PORT` env overrides (9001 for BDS dp, for example) until the old deployment retires. The shifted numbers go in that repo's rollout doc or `instances/README.md`, and `instance.json` keeps the scheme numbers.

## Host access

A host reaches Gitea with its own SSH key, added as a **read-only deploy key** on each repo it deploys. Never put a host's key on a person's or the bot account: it breaks when that account's access changes, and it grants more than the host needs. Servers (prep and prod, `gitea-workflows` Environments) pull release images with a package-read token instead of source. Images publish by channel (`:prep` from `prep`, `:X.Y.Z` from a release tag; `gitea-workflows`, Images), so a host deploys with `docker compose pull && docker compose up -d`: compose files and `instances/` come from its read-only clone, env files stay on the host, and nothing is built on the server. The hosts, what each deploys, and the commands to add one are in WIKI `systems_networking/Hosts/README.md`.

## Done when

- The rollout doc names backup, move, verification and rollback commands before the first command runs.
- Row counts per database match before and after the move.
- One scheduled tick completes on the new layout.
