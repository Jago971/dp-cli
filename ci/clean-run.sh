#!/usr/bin/env bash
# Removes the containers and networks a CI job's scripts started, by the run
# label the smoke-test contract puts on them. The runner shares the host's
# Docker, and a step killed by its timeout never reaches its own cleanup.
#
#   ci/clean-run.sh <run-label>
set -euo pipefail

LABEL="datumpin.ci-run=$1"
CONTAINERS=$(docker ps -aq --filter "label=$LABEL")
NETWORKS=$(docker network ls -q --filter "label=$LABEL")

if [[ -n "$CONTAINERS" ]]; then
  # shellcheck disable=SC2086
  docker rm -f $CONTAINERS >/dev/null
fi
if [[ -n "$NETWORKS" ]]; then
  # shellcheck disable=SC2086
  docker network rm $NETWORKS >/dev/null
fi
echo "CLEAN  $LABEL: $(wc -w <<<"$CONTAINERS") containers, $(wc -w <<<"$NETWORKS") networks"
