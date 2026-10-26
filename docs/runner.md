# The Actions runner

**Scope:** The Gitea Actions runner on Hammond: what runs, how to start, upgrade and roll it back, and the Docker settings CI depends on. Not the workflows themselves (see the `gitea-workflows` skill).
**Status:** current
**Last reviewed:** 2026-10-20

---

## What runs

| | |
|---|---|
| Host | Hammond (`192.168.10.101`) |
| Container | `gitea-runner`, restart `unless-stopped` |
| Image | `docker.io/gitea/runner:5` (the `5` tag follows the newest 5.x; v5.1.1 on 2026-10-20) |
| Registration | `hammond-runner`, id 16, in the `act_runner_data` volume at `/data/.runner` |
| Labels | `ubuntu-latest`, `ubuntu-24.04`, `ubuntu-22.04`, each a `docker.gitea.com/runner-images` job image |
| Docker | The host's socket is mounted, so jobs run as sibling containers on Hammond's Docker |
| Config | `/data/config.yaml` in the volume: `capacity: 2` (two jobs at once); everything else is the default |

The image was `gitea/act_runner` up to v0.6.1; it is now `gitea/runner`, and the binary is `gitea-runner`. A Gitea 28 server needs a current runner for reusable workflows shared across repos.

Every job's `runs-on` must match a label (`ubuntu-latest` in every repo today); since 5.0 a job with no match fails instead of falling back.

## Start

Run as a user in the `docker` group. The registration token is only read when `/data/.runner` is missing; it comes from Gitea Site Administration > Actions > Runners and is never written to a file that stays.

```bash
umask 077; ENVF=$(mktemp)
printf '%s\n' \
  GITEA_INSTANCE_URL=http://192.168.10.101:3393 \
  GITEA_RUNNER_NAME=hammond-runner \
  "GITEA_RUNNER_REGISTRATION_TOKEN=<token>"   CONFIG_FILE=/data/config.yaml > "$ENVF"
docker run -d --name gitea-runner --restart unless-stopped --env-file "$ENVF" \
  -v act_runner_data:/data -v /var/run/docker.sock:/var/run/docker.sock \
  docker.io/gitea/runner:5
rm -f "$ENVF"
docker logs gitea-runner 2>&1 | tail -3   # "... with version: v5.x.y ... declare successfully"
```

Capacity: Hammond has 4 cores and 11 GB; two concurrent jobs leave room for the services it hosts. Raise `capacity` in `/data/config.yaml` and restart the container to change it; a second runner, on another machine, is the next step if CI outgrows that.

## Upgrade

1. Check no job is running (Gitea Site Administration > Actions > Runners, or each repo's Actions tab).
2. Read the release notes' breaking changes: <https://gitea.com/gitea/runner/releases>.
3. `docker pull docker.io/gitea/runner:5`
4. `docker stop gitea-runner && docker rename gitea-runner gitea-runner-old`
5. Start it as above. The registration in the volume is kept, so no token is needed.
6. When a job has run, `docker rm gitea-runner-old`.

A new major version (6) changes the tag in step 3 and in Start.

## Roll back

`docker stop gitea-runner && docker rm gitea-runner && docker rename gitea-runner-old gitea-runner && docker start gitea-runner`. The registration file format is unchanged across versions.

## Docker settings CI depends on

The registry is plain HTTP on port 3393, so Docker on Hammond lists it as an insecure registry in `/etc/docker/daemon.json`:

```json
{ "insecure-registries": ["192.168.10.101:3393"] }
```

Changing it needs sudo and a Docker restart, which briefly stops every container on Hammond; all of them restart on their own (`always` or `unless-stopped`). Serving Gitea over TLS removes this setting (DEVKIT#15).

## Known limits

The runner image has no LibreOffice, so a PDF test that needs it skips in `python-tests` (AHJ). Add it to the image if a repo needs that test to run in CI.

## History

- 2026-10-20: `gitea/act_runner:latest` (v0.6.1) replaced by `gitea/runner:5` (v5.1.1), same registration (DEVKIT#7).
- 2026-10-20: capacity 1 → 2 through `/data/config.yaml`.
