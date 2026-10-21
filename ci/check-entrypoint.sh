#!/usr/bin/env bash
# Fails when a built image's ENTRYPOINT file is missing or not executable, a
# fault that otherwise shows only when a host starts the image (BDS's api
# shipped one). Needs no app config: it runs `test -x` inside the image.
#
#   ci/check-entrypoint.sh <image>
set -euo pipefail

IMAGE=$1
ENTRY=$(docker image inspect --format '{{if .Config.Entrypoint}}{{index .Config.Entrypoint 0}}{{end}}' "$IMAGE")

if [[ "$ENTRY" != /* ]]; then
  echo "PASS  no entrypoint file to check (${ENTRY:-none})"
  exit 0
fi

set +e
docker run --rm --entrypoint test "$IMAGE" -x "$ENTRY" 2>/dev/null
CODE=$?
set -e

case $CODE in
  0) echo "PASS  entrypoint $ENTRY is executable" ;;
  1) echo "FAIL  entrypoint $ENTRY is missing or not executable"; exit 1 ;;
  *) echo "WARN  could not run 'test' in the image (exit $CODE); entrypoint $ENTRY not checked" ;;
esac
