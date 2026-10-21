#!/usr/bin/env bash
# Pushes a built image under each tag and leaves the host's Docker as it found
# it: the runner shares the host's daemon, where deployed stacks run from
# those same tags (`:prep`), so a tag that pointed at an image before the push
# points at it again afterwards, and one that did not exist is removed. The
# caller logs in first and removes the local tag afterwards.
#
#   ci/push-image.sh <local-tag> <tag>...
set -euo pipefail

LOCAL=$1
shift

for TAG in "$@"; do
  BEFORE=$(docker image inspect --format '{{.Id}}' "$TAG" 2>/dev/null || true)
  docker tag "$LOCAL" "$TAG"
  docker push "$TAG" && PUSHED=yes || PUSHED=no
  if [[ -n "$BEFORE" ]]; then
    docker tag "$BEFORE" "$TAG"
  else
    docker image rm "$TAG" >/dev/null
  fi
  [[ $PUSHED == yes ]] || { echo "FAIL  push of $TAG"; exit 1; }
  echo "PUSHED  $TAG${BEFORE:+ (host tag kept on its image)}"
done
