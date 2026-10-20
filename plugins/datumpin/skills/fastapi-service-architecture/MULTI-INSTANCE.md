# One codebase, several instances

Parent: [SKILL.md](SKILL.md). When one service runs for more than one product or customer (BDS's `api` serving `dp` and `rur`), the default is one codebase deployed as several compose services through config.

- **What varies per instance:** the database connection, env-driven config, and generalised schema columns (a nullable self-referential grouping column one instance uses and another leaves null). One schema serves every instance.
- **What stays fixed:** the codebase. Every fix lands once.
- **Each instance is isolated by deployment:** its own database, env file and migration history (Alembic per service, own history per instance), and no runtime dependency on another instance.
- **Infrastructure services** (decode and orchestration with no business schema, such as a processor) follow the same pattern.
- **An instance's identity derives from its mount.** BDS's instances write clean data and change logs under their own `instances/<name>/data/`, found through the one `INSTANCE_DIR` mount. A second env var such as `CLEAN_DATA_DIR` could be set inconsistently, and a shared default output path collides when two instances run side by side.
- **Input isolation differs from output isolation, and the doc says so.** Both BDS instances read one raw-data directory, mounted read-only from outside the instance folder. Each instance's customer-identity filter decides which files it owns, since there is one real raw data lake.
- **An instance with no seed content comes up schema-current but empty.** Its loader reads only its own `seeds/`, and an empty manifest means nothing to seed. Seeding patterns live in `config-led-deployment` ("Seeding"). Add id write-back only when the seed files reference each other by position.
- **Compose profiles** (`["dp"]`, `["rur"]`) start one instance or both from one generated file. See `config-led-deployment` and `docker-compose-conventions`.

## Done when

- A second instance, booted, shows its own identity and its own row counts, and the first instance's counts and DB file mtime are unchanged.
- `grep -rniE "\b(dp|rur)\b" --include=*.py .` finds no instance name in service code.
