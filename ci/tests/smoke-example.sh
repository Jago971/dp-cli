#!/usr/bin/env bash
# An image smoke test in the shape docker-image's `smoke-test` input runs:
# it takes the built image's tag, starts the image on a throwaway network,
# makes its requests from another container on that network, and exits 1 on
# a failure. Never through host ports: a CI job is itself a container beside
# the image, so the host's loopback is out of its reach. Everything it starts
# carries the job's run label, so clean-run.sh removes it even when the step
# is killed before the trap runs.
#
#   smoke-example.sh <image>
set -euo pipefail

IMAGE=$1
# A random suffix: concurrent CI jobs share the runner's Docker, and each
# job's $$ can repeat.
RUN=smoke-$(od -An -N4 -tx1 /dev/urandom | tr -d ' \n')
LABEL="datumpin.ci-run=${CI_RUN_LABEL:-local}"

cleanup() {
  docker rm -f "$RUN" >/dev/null 2>&1 || true
  docker network rm "$RUN" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker network create --label "$LABEL" "$RUN" >/dev/null
docker run -d --label "$LABEL" --name "$RUN" --network "$RUN" "$IMAGE" >/dev/null

for _ in $(seq 20); do
  if docker run --rm --label "$LABEL" --network "$RUN" alpine:3.20 wget -q -T 2 -O- "http://$RUN:8080/" 2>/dev/null | grep -q ok; then
    echo "PASS  / answers"
    exit 0
  fi
  sleep 0.5
done
echo "FAIL  / did not answer on port 8080"
exit 1
