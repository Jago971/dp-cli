---
name: docker-compose-conventions
description: Dockerfiles and compose files - dev/prod split, multi-stage builds, anonymous volumes, restart policy, non-root users. Nginx frontend images go to frontend.md, cron services to cron.md; a laptop without registry access goes to local-packages.md.
---

# Docker & Compose conventions

Env files, ports, networks and the ownership entrypoint belong to `config-led-deployment`. Build-time credentials belong to `secrets-handling`. This skill owns Dockerfile and compose mechanics.

Branches that load a sibling file:

- A prod frontend served by nginx: [frontend.md](frontend.md).
- A service that runs cron: [cron.md](cron.md).
- A dev machine whose Docker cannot reach the private registry: [local-packages.md](local-packages.md).

## Two environments

Each environment has its own Dockerfile and compose file: `Dockerfile` + `docker-compose.yml` (prod), `Dockerfile.dev` + `docker-compose.dev.yml` (dev). Distinct `container_name` and image tags (`-prod` against `-prep`/`-dev`) keep them apart. Run one environment per host, because their ports collide.

Where a repo has several instances, `scripts/compose.py` generates the compose files from the instance folders, and each instance starts with its own env file through `--env-file` (see `config-led-deployment`).

## Prod: multi-stage builds

The builder stage installs and builds. The final stage copies only the built artifact into a minimal runtime image, so source, `node_modules` and build caches stay in the builder.

```dockerfile
FROM node:20.20-slim AS builder
...
FROM nginxinc/nginx-unprivileged:1.31-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

The full frontend serve stage (proxy template, port, compose) is in [frontend.md](frontend.md).

## Dev: anonymous volumes protect installed dependencies

When bind-mounting source for hot reload, pin dependency directories as anonymous volumes so the host mount cannot shadow the container-built ones (native bindings differ by platform).

```yaml
volumes:
  - ./services/api:/app
  - /app/venv          # anonymous volume: protects the container's own venv
```

Compose reattaches a service's existing anonymous volume to its recreated container, so `--build`, `--force-recreate` and `--no-cache` all leave stale dependencies in place. After a dependency change, run `docker compose rm -fsv <service>` (removes the container and its anonymous volumes), then `up -d --build`.

A build output folder the container writes inside a bind-mounted source tree (`./frontend/dist`) is an anonymous volume (`/app/dist`) that the Dockerfile created owned by the app user. The host folder keeps its own permissions.

## Env changes need a recreated container

`docker compose restart` keeps the container's creation-time environment. After editing an env file, run `docker compose up -d <service>`, which recreates the container against the current file.

## Restart policy

`restart: unless-stopped` goes on every service in both compose files, so containers return after an engine restart.

## Non-root, consistently

Every service container that mounts an instance folder runs the ownership `docker-entrypoint.sh` from `config-led-deployment`: it starts as root, adopts the owner of the mounted instance folder, and drops to that uid:gid before `exec`ing the app. The image also creates `appuser` as the fallback for a root-owned mount, and as the whole rule for a service that mounts no instance folder:

```dockerfile
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
```

- Prod and dev Dockerfiles both create `appuser`.
- Every writer to a shared bind-mounted directory uses the same non-root uid. The first user a Debian-based image creates gets uid 1000, so separate images agree without coordination.
- Node frontends run by `npm run dev` create `appuser` too. A prod frontend runs as nginx-unprivileged's own user ([frontend.md](frontend.md)).
- Ports below 1024 need root. A non-root service listens on a port of 1024 or more inside the container (3000 for a frontend, 8000 for an api), and compose maps the host side unchanged.
- A service that runs cron keeps the daemon as root: see [cron.md](cron.md).

## BuildKit

Start Dockerfiles with `# syntax=docker/dockerfile:1`. Build-time credentials use secret mounts scoped to one `RUN` layer (see `secrets-handling`).

## SBOM

Every image carries its software bill of materials at `/sbom.json`, built in the image: `cyclonedx-py` for Python, `@cyclonedx/cyclonedx-npm` in a frontend's builder stage. Every repo gitignores `sboms/`.

- A backend container, and a dev frontend, also writes a dated copy at boot into `./sboms:/sboms`.
- A prod frontend runs as nginx-unprivileged's user, which cannot write the host's `./sboms`, so it carries the SBOM without exporting it and mounts no `./sboms`. Fetch it with `docker cp <container>:/sbom.json <file>`.
- `docker-image` sends every image's SBOM to Dependency-Track when the org variable `DEPENDENCY_TRACK_URL` is set (`gitea-workflows`, Images).

## Done when

- `docker compose -f <file> config -q` passes for every compose file you touched.
- `grep -c "restart:" docker-compose*.yml` equals the service count in each file.
- `grep -L "^USER" Dockerfile*` lists only images that drop privileges in an entrypoint or run as their base image's own non-root user (nginx-unprivileged).
- After an env change, `docker exec <container> printenv <VAR>` shows the new value.
- After a dependency change, the new package is present inside the running container (`docker exec <container> ...`).
