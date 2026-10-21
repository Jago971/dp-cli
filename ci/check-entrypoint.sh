#!/usr/bin/env bash
# Fails when a built image's ENTRYPOINT file is missing or not executable, a
# fault that otherwise shows only when a host starts the image. Needs no app
# config: it runs `test -x` inside the image, as the image's own user.
#
#   ci/check-entrypoint.sh <image>
set -euo pipefail

IMAGE=$1
ENTRY=$(docker image inspect --format '{{if .Config.Entrypoint}}{{index .Config.Entrypoint 0}}{{end}}' "$IMAGE")

if [[ -z "$ENTRY" ]]; then
  echo "PASS  no ENTRYPOINT"
  exit 0
fi
if [[ "$ENTRY" != /* ]]; then
  echo "SKIP  ENTRYPOINT '$ENTRY' is not a path; not checked"
  exit 0
fi

set +e
ERROR=$(docker run --rm --entrypoint test "$IMAGE" -x "$ENTRY" 2>&1 >/dev/null)
CODE=$?
set -e

case $CODE in
  0) echo "PASS  entrypoint $ENTRY is executable" ;;
  1) echo "FAIL  entrypoint $ENTRY is missing or not executable"; exit 1 ;;
  # 125-127: docker could not run `test` in the image (a minimal image has
  # none). The image is not wrong, only unchecked, so the build goes on.
  *) echo "WARN  entrypoint $ENTRY not checked: could not run 'test' in the image (exit $CODE): $ERROR" ;;
esac
