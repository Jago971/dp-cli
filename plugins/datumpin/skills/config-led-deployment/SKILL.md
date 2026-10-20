---
name: config-led-deployment
description: Instance folders - adding a product instance, or changing how instances are configured, seeded, ported, networked or compose-generated. Frontend branding goes to branding.md, a live-server restructure or host access to rollout.md, service code layering to fastapi-service-architecture.
---

# Config-led deployment

One codebase per app, one folder per instance (BDS `bds-dp`/`bds-rur`, AHJ `ahj-dp`/`ahj-rur`, curator `curator-dp`/`curator-rur`). Every Datumpin repo follows this skill, and a new pattern lands here in the same change that introduces it.

**Terms.** An *app* is a codebase (`ahj`, `curator`, `bds`). An *instance* is one deployment of it (`dp`, `rur`). A *service* is one container of an instance (`backend`, `frontend`; BDS's `api`, `processor`). Names run app first, then instance.

Branches that load a sibling file:

- Frontend branding (theme tokens, logos): [branding.md](branding.md).
- Restructuring a live server, running beside an older deployment, or giving a host access to a repo: [rollout.md](rollout.md).

## Two kinds of config

- **Infrastructure config** says how an instance reaches its dependencies (API base URL, DB connection string, timeouts). Every field is required, with no default.
- **Content/branding config** says what an instance looks like. The instance supplies it as files, and a missing required file stops startup.

Keep them as separate config objects. PACKAGES' `docs/reference/config-convention.md` holds the reasoning. This skill covers delivering either kind to an instance through env files and mounted files.

## The instance folder: one generic shape, different content

Everything specific to one instance lives in `instances/<name>/`, with the same shape for every instance. The code never names an instance, and a new instance is a new folder. One folder serves all of the instance's services (BDS's api and processor mount the same one). AHJV2's `instances/README.md` is the worked example.

```
instances/<name>/
├── seeds/            what the instance seeds from (+ manifest.json = the load order)
├── customers/        <customer_code>.json
├── branding/         theme.css and logo pictures (see branding.md)
├── word_templates/   <style>.docx brand templates
├── data/             everything the services write: SQLite file, clean data, change logs (gitignored)
└── instance.json     host ports (dev and prod, every service) and the `assets` block
instances/_template/  neutral skeleton to copy for a new instance
```

A smaller app has fewer kinds of data: curator's folder is `branding/`, `data/` and `instance.json`; BDS's is `seeds/`, `data/` and `instance.json`.

- **Env files stay at the repo root** (see "Env files"). Assets, seeds, branding, templates and output data live in the folder.
- **Output data lives under `data/`**, gitignored. The DB file has the same name in every instance (`data/ahj.db`, `data/curator.db`, BDS's `data/api.db`). Shared raw input (BDS's raw-data lake) stays outside the folder and mounts read-only through an explicit mount.
- **One shared package reads the folder.** Every repo uses `datumpin-instance-config` (PACKAGES) for path safety, the public-content check on `branding/`, the required `theme.css` tokens and the `assets` block. Callers pass their instance's folder, and the app owns where the folder is and how it is laid out.
- **One mount, one env var.** Compose mounts `./instances/<name>` at `/instance` and sets `INSTANCE_DIR=/instance` as a constant in the service definition. One small module (`instance.py` or the settings class) is the only code that knows the folder's layout. The DB default derives from the mount (`data/<app>.db`), and an explicit `*_DATABASE_URL` overrides it (tests).
- **Name for peers.** Defaults, file names, network names and doc wording are instance-neutral. Every instance gets the same naming shape (`ahj-dp`, `ahj-rur`).
- **Run every service container as the folder's owner.** All services, BDS's api and processor included, use one `docker-entrypoint.sh` (the gosu pattern of the official postgres and redis images):
  1. Start as root and `stat` the mounted instance folder.
  2. Hand the runtime-state folders (`data/`, `outputs/`, `static/`, and `seeds/` where seeding writes ids back) to that uid:gid.
  3. Drop to it with `setpriv` before `exec`ing the real command.
  4. Fall back to the image's own user when the mount is root-owned (Docker Desktop shows bind mounts that way), and just run when already unprivileged.

  Route each service's compose `entrypoint:` through the script, keep `*.sh` LF (`.gitattributes`), and test both paths (a volume owned by an arbitrary uid, and a root-owned mount). Production prefers a named volume for the DB over a host-owned bind mount.

### The `_template` rule

`instances/_template/` is a neutral skeleton. Its `instance.json` carries every required key as `null` or a placeholder, with no real ports, so a copy cannot collide with a running instance until its owner fills it in. The generator skips folders starting with `_` and fails fast on a real instance whose required keys are still null. The rest of the skeleton is monochrome branding and only what the app needs.

## Seeding: two patterns, chosen by the kind of data

`fastapi-service-architecture` describes the same two patterns and stays consistent with this section.

- **Authored documents/blocks (AHJ): `instances/<name>/seeds/` with a `manifest.json` load order and id write-back.** The instance owns its seed tree and writes the ids it assigns back into it, locally and on a server. Seed each instance from its own folder. Content two instances share (a customer's seeds) is duplicated per instance, so neither's ids can overwrite the other's.
- **Reference/curation data keyed by natural key (BDS): `instances/<name>/seeds/*.csv`.** The loader is idempotent: it skips rows that already exist, never overwrites curated data, and writes no ids back. `manifest.json` gives the load order, where a listed file that is missing stops startup and an unlisted file is ignored. First boot seeds an empty database, and an explicit container command seeds a running one.
- **No seeds (curator).** Its curation data lives in BDS, and it keeps a small DB for its own roles.

The loader reads the instance's own folder, never another instance's and never a hardcoded file list. An instance with nothing to seed comes up schema-current but empty.

## Env files

Env files stay at the repo root, one pair per instance: `.env.<app>-<instance>` (prod) and `.env.<app>-<instance>.dev`, app first (`.env.ahj-dp`, `.env.curator-dp`, `.env.bds-dp`, `.env.bds-rur`). BDS is one app, so its api and processor share one file per instance and differ by prefix (`API_`, `PROCESSOR_`). Every instance gets its own named file.

Each file holds everything that instance's containers need: its own settings and its own copy of any build-time secret (a registry token). Tracked `.env.<app>-<instance>.example` files document each file's shape, and the real files are gitignored. Wire the file into each service with `env_file:` and start an instance with an explicit `--env-file`:

```
docker compose --env-file .env.ahj-dp.dev -f docker-compose.dev.yml --profile dp up -d
docker compose --env-file .env.ahj-rur.dev -f docker-compose.dev.yml --profile rur up -d
```

Build secrets resolve from that same file (see `secrets-handling`). The settings class stays generic: one `env_prefix` per codebase, every field required (see `fastapi-service-architecture`, "Typed settings"). What differs per instance is which file a container reads. Instance-specific display values such as the service title are required settings in the env file.

An env-file change takes effect after the container is recreated (`docker compose up -d <service>`, see `docker-compose-conventions`).

## Host ports, per instance, in `instance.json`

`instances/<name>/instance.json` holds the dev and prod host port of every service (`dev_backend_port`, `prod_backend_port`, `dev_frontend_port`, ... for AHJ and curator; `dev_api_port`, `dev_processor_port`, ... for BDS where a service publishes one). The generator turns each into a default, such as `"${AHJ_DP_BACKEND_HOST_PORT:-8000}:8000"`, so a host with that port taken can override it. The override variable is `<APP>_<INSTANCE>_<SERVICE>_HOST_PORT`, lives in that instance's env file, and takes effect only when passed through `--env-file`, because compose interpolates `${VAR}` from that file alone.

One block of host ports per app, and the instance picks the last digit (1 = dp, 2 = rur, then 3, ...). Dev and prod use the same number, and the container-internal port is the same in every instance.

| Block | App | Ports |
|---|---|---|
| 80xx | BDS backends | 8001 dp, 8002 rur |
| 81xx | Curator backends | 8101, 8102 |
| 82xx | AHJ backends | 8201, 8202 |
| 52xx | AHJ frontends | 5201, 5202 |
| 53xx | Curator frontends | 5301, 5302 |

A new app takes the next free block. A server running beside an older live deployment shifts by +1000 (see [rollout.md](rollout.md)).

## Compose generation: a profiled library in one file

Tag each instance's services with a Compose `profiles:` entry (`profiles: ["dp"]`) instead of copying a second compose file. `docker compose --profile dp up -d` starts one instance, and naming both profiles starts both.

`scripts/compose.py` generates the compose files from the instance folders. Each repo has a small, dependency-free copy that writes the dev, prod and local-packages files from templates, one service group per instance folder (folders starting with `_` are skipped). The group is a backend + frontend pair for AHJ and curator and an api + processor pair for BDS. Service, network, profile, env-file and port-variable names all derive from the folder name.

- The files carry a **generated** header and change only through the templates or an `instance.json`, followed by a regenerate.
- `--check` exits non-zero when the files on disk are stale, and CI runs it in every repo.
- The `-prep`/`-prod` container-name suffixes and explicit read-only mounts of shared raw input stay where the repo has them.
- Adding an instance: copy `_template`, fill it in, add its env files, run the script.
- Without host Python, run it in a throwaway container: `docker run --rm -v "$PWD:/w" -w /w python:3.11-slim python scripts/compose.py`.

## Networks: per instance, per consumer

The externally facing network is per instance and per consumer, named `<instance>-<consumer>-net`: `dp-ahj-net` (the dp BDS instance serving AHJ), `dp-curator-net`, `rur-curator-net`. A network is a separate trust boundary for one consumer of one instance, and consumers never share one across instances. The old shared `bds-net` is retired for consumers.

Use those per-instance external networks plus the compose default network, since services of one instance already reach each other on the default. AHJ and curator follow this. BDS keeps an internal per-instance `bds-<instance>-net` for api <-> processor, and its ops doc says why. No consumer attaches to it, and no instance's data crosses to another instance over it.

A network name shared between two repos is a cross-repo contract. Each repo declares it in its own compose file, and nothing checks the two strings match until a container resolves the other by hostname, at which point a mismatch shows up as `socket.gaierror: Temporary failure in name resolution`. Confirm the exact string in both repos' compose files, then check from the running host.

## Done when

- `python scripts/compose.py --check` exits 0.
- `docker compose --env-file .env.<app>-<instance> config -q` resolves with no unset-variable warning.
- `instances/_template/instance.json` holds no real ports.
- `docker inspect <container> --format '{{json .NetworkSettings.Networks}}'` on a consumer and on its api shows the same network name.
- A second instance, booted, shows its own identity (title, `.db` file name) and its own row counts, and the first instance's row counts and DB file mtime are unchanged.
