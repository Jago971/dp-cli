#!/usr/bin/env bash
# An image smoke test in the shape docker-image's `smoke-test` input runs:
# it takes the built image's tag, starts the image on a throwaway network,
# makes its requests from another container on that network, and exits 1 on
# a failure. Never through host ports: a CI job is itself a container beside
# the image, so the host's loopback is out of its reach.
#
#   smoke-example.sh <image>
set -euo pipefail

IMAGE=$1
RUN=smoke-$$

cleanup() {
  docker rm -f "$RUN" >/dev/null 2>&1 || true
  docker network rm "$RUN" >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker network create "$RUN" >/dev/null
docker run -d --name "$RUN" --network "$RUN" "$IMAGE" >/dev/null

for _ in $(seq 20); do
  if docker run --rm --network "$RUN" alpine:3.20 wget -q -O- "http://$RUN:8080/" 2>/dev/null | grep -q ok; then
    echo "PASS  / answers"
    exit 0
  fi
  sleep 0.5
done
echo "FAIL  / did not answer on port 8080"
exit 1
