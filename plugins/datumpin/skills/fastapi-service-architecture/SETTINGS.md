# Typed settings

Parent: [SKILL.md](SKILL.md). Use `pydantic-settings`, one `Settings` class per service.

- **Infrastructure config is typed, and every field is required.** A missing setting stops startup with a message naming it. The one allowed default derives from the instance mount (the DB URL, `data/<app>.db` under `INSTANCE_DIR`).
- **Optional integrations are `Optional[...] = None` and default off.** Mail credentials, a third-party API key and a dev identity are examples. An absent value turns the feature off.
- **CORS:** a service no browser calls directly keeps `API_CORS_ORIGINS` as a required setting, where an explicit empty value means no cross-origin callers. Curator's frontend proxies `/api` to its own backend and AHJ's frontend calls AHJ's backend, so BDS needs no browser origins.
- **One generic `env_prefix` per codebase**, named for the codebase and never for a product or instance: `AHJ_`, `CURATOR_`, and for BDS `API_` / `PROCESSOR_`. A stray prefix (BDS's `BDS_ENABLE_DEV_RESET`) folds under the codebase prefix. Every instance uses the same prefix, and what differs per instance is the env file the container reads (`.env.<app>-<instance>`, wired through compose `env_file:`). See `config-led-deployment`.
- **Instance-specific display values** (a service title) are required env settings. `instance.json` holds ports and assets only.
- **Validate at import time**, so an invalid config fails on container start.
- **Name a field so it does not repeat its prefix.** `env_prefix` concatenates with the field name: `api_title` under `API_` expects `API_API_TITLE`, and pydantic-settings silently falls back to the field's default. Use `title`.

## Done when

- `python -c "import config"` with an empty environment fails and names the first missing variable.
- No field name starts with its own prefix.
- Each field is required, `Optional[...] = None`, or derived from the instance mount.
- Booting a second instance with the variable set shows the value taking effect.
