---
name: secrets-handling
description: Secrets - adding env vars, .env files, credentials, Docker build secrets or CI secrets. What is committed, and keeping credentials out of image layers.
---

# Secret handling

## Env files

Real env files are gitignored (`.env.*` except `.env.*.example`). Each has a committed `.env.<app>-<instance>.example` beside it. Naming and layout live in `config-led-deployment`.

- Comment every variable in the `.example`, including non-obvious math (`604800   # 60 * 60 * 24 * 7, one week`). Group by service for multi-service projects.
- Mark an undecided default `# TODO: confirm default`.
- Non-secret allowlists (notification recipients) live in a versioned data file, so a diff shows changes to them.
- One `docs/reference/ops/environment-variables.md` table (variable / default / what reads it / purpose) is the only variable list. Ops docs link to it.

## Settings fail fast

Typed settings with every field required follow `fastapi-service-architecture` ("Typed settings"). Two secret-specific rules:

- A secret for an optional integration (mail credentials, a service API key) is `Optional[...] = None`, and an absent value turns the integration off.
- A blank env var and an unset one are different in some settings libraries. Add an explicit validator where the library treats them the same.

## Build-time credentials

Pass them through BuildKit secret mounts, which never touch an image layer:

```dockerfile
# syntax=docker/dockerfile:1
RUN --mount=type=secret,id=gitea_token \
    GITEA_TOKEN=$(cat /run/secrets/gitea_token) \
    pip install --extra-index-url ... -r requirements.txt
```

`ARG` and `ENV` values persist in layer history, where anyone with the image can read them. Build credentials are scoped, package-read-only tokens.

Compose resolves the `secrets:` entries (`environment: GITEA_TOKEN`) from the instance's own file passed with `docker compose --env-file .env.<app>-<instance>[.dev]`, and each instance's file carries its own copy of the registry credentials (see `config-led-deployment`).

## Per environment

Who holds which secret in each environment. The environments' hosts and env-file names are in `gitea-workflows`, Environments; host keys in `config-led-deployment`, rollout.md; CI's secrets in `gitea-workflows`.

| Secret | dev | prep and prod |
|---|---|---|
| App settings and service keys | the developer, dev values only | the host; prod's stay host-only until a secret store is chosen |
| Registry read | the developer's package-read token, where Docker reaches the registry; otherwise none (`local-packages.md`) | the host's package-read token |
| Registry write | nobody: CI publishes | nobody: CI publishes |
| Gitea source | the developer's SSH key | the host's read-only deploy key |

- Each environment holds its own values; a value never moves between them.
- Servers hold read-only tokens; publishing and every other write happen in CI, whose org secrets reach workflows (exposure from branch PRs: #102).
- An env file stays on its host.

## CI secrets

Workflows reference required secrets by name. See `gitea-workflows` for stating missing ones.

## Done when

- `git ls-files | grep -E '^\.env'` lists only `*.example` files.
- `docker history --no-trunc <image>` shows no token value.
- Every variable in each `.example` has an inline comment.
- `git grep` for the token's prefix finds nothing.
- A server's env file holds no write-scoped token.
