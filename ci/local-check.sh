#!/usr/bin/env bash
# Runs, on your own Docker and in containers only, every check DEVKIT's CI
# runs on a PR (ci.yml and security-scan.yml), so a change is checked before
# it is pushed; CI then runs them again. Tool versions are read from those
# workflows, so each one is set in one place. Prints one PASS or FAIL line per
# check and exits 1 when any fails.
#
#   ci/local-check.sh        (from the DEVKIT root)
set -uo pipefail

export MSYS_NO_PATHCONV=1  # Git Bash on Windows would rewrite the container paths
ROOT=$(pwd)
FAILED=0

# The value of KEY: "value" in a workflow file.
pin() { sed -n "s/^ *$2: \"\(.*\)\"/\1/p" ".gitea/workflows/$1" | head -n 1; }

check() {
  local name=$1; shift
  local log
  log=$(mktemp)
  if "$@" >"$log" 2>&1; then
    echo "PASS  $name"
  else
    echo "FAIL  $name"
    tail -n 20 "$log" | sed 's/^/      /'
    FAILED=1
  fi
  rm -f "$log"
}

in_repo() { docker run --rm -v "$ROOT:/w:ro" -w /w "$@"; }

check "pytest (ci/tests)" docker run --rm -e PYTHONDONTWRITEBYTECODE=1 \
  -v /var/run/docker.sock:/var/run/docker.sock -v "$ROOT/ci:/w/ci" -w /w/ci/tests python:3.12-alpine \
  sh -c 'apk add -q bash docker-cli && pip install -q -r requirements.txt && python -m pytest -q -p no:cacheprovider -m "unit or integration"'
check "conformance" in_repo python:3.11-alpine python ci/conformance.py .
check "versions" in_repo python:3.11-alpine python ci/versions.py .
check "hook compiles" in_repo -e PYTHONDONTWRITEBYTECODE=1 python:3.11-alpine \
  python -c 'import ast; ast.parse(open("plugins/datumpin/hooks/session_status.py").read())'
check "actionlint" in_repo "rhysd/actionlint:$(pin ci.yml ACTIONLINT_VERSION)" -color .gitea/workflows/*.yml
check "gitleaks" in_repo "zricethezav/gitleaks:v$(pin security-scan.yml GITLEAKS_VERSION)" dir --redact --no-banner /w
check "osv-scanner" in_repo "ghcr.io/google/osv-scanner:v$(pin security-scan.yml OSV_SCANNER_VERSION)" \
  scan source --recursive --no-resolve /w
check "plugin validate" in_repo node:22-alpine sh -c \
  "npm install --global --silent @anthropic-ai/claude-code@$(pin ci.yml CLAUDE_CODE_VERSION) && claude plugin validate ./plugins/datumpin && claude plugin validate ."

exit "$FAILED"
