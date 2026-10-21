#!/usr/bin/env bash
# Runs, on your own Docker and in containers only, every check DEVKIT's CI
# runs on a PR (ci.yml and security-scan.yml), so a change is checked before
# it is pushed; CI then runs them again. Tool versions are read from those
# workflows, so each one is set in one place. Prints one PASS or FAIL line per
# check and exits 1 when any fails. Commit first: gitleaks scans the commits
# since origin/prep, as CI scans a PR's.
#
#   ci/local-check.sh        (from the DEVKIT root)
# No -e: one failing check must not stop the rest; check() records it.
set -uo pipefail

# Git Bash on Windows rewrites /w-style container paths unless told not to.
export MSYS_NO_PATHCONV=1
ROOT=$(pwd)
LOGS=$(mktemp -d)
trap 'rm -rf "$LOGS"' EXIT
FAILED=0

# The value of KEY: "value" in a workflow file; stops when it is missing.
pin() {
  local value
  value=$(sed -n "s/^ *$2: \"\(.*\)\"/\1/p" ".gitea/workflows/$1" | head -n 1)
  [[ -n "$value" ]] || { echo "local-check: no $2 in .gitea/workflows/$1" >&2; exit 2; }
  echo "$value"
}
ACTIONLINT=$(pin ci.yml ACTIONLINT_VERSION) || exit 2
CLAUDE_CODE=$(pin ci.yml CLAUDE_CODE_VERSION) || exit 2
GITLEAKS=$(pin security-scan.yml GITLEAKS_VERSION) || exit 2
OSV_SCANNER=$(pin security-scan.yml OSV_SCANNER_VERSION) || exit 2

check() {
  local name=$1 log="$LOGS/$1"; shift
  if "$@" >"$log" 2>&1; then
    echo "PASS  $name"
  else
    echo "FAIL  $name"
    tail -n 20 "$log" | sed 's/^/      /'
    FAILED=1
  fi
}

in_repo() { docker run --rm -v "$ROOT:/w:ro" -w /w "$@"; }

# Exit 128 means no requirements file or lockfile to scan, which CI passes.
osv_scan() {
  in_repo "ghcr.io/google/osv-scanner:v$OSV_SCANNER" scan source --recursive --no-resolve /w
  local code=$?
  [[ $code -eq 128 ]] && return 0
  return "$code"
}

check pytest docker run --rm -e PYTHONDONTWRITEBYTECODE=1 \
  -v /var/run/docker.sock:/var/run/docker.sock -v "$ROOT/ci:/w/ci" -w /w/ci/tests python:3.11-alpine \
  sh -c 'apk add -q bash docker-cli && pip install -q -r requirements.txt && python -m pytest -m "unit or integration"'
check conformance in_repo python:3.11-alpine python ci/conformance.py .
check versions in_repo python:3.11-alpine python ci/versions.py .
check hook in_repo python:3.11-alpine python -c \
  'p = "plugins/datumpin/hooks/session_status.py"; compile(open(p).read(), p, "exec")'
check actionlint in_repo "rhysd/actionlint:$ACTIONLINT" -color .gitea/workflows/*.yml
check gitleaks in_repo --entrypoint sh "zricethezav/gitleaks:v$GITLEAKS" -c \
  'git config --global --add safe.directory /w && gitleaks git --redact --no-banner --log-opts="origin/prep..HEAD" /w'
check osv-scanner osv_scan
check plugin in_repo node:22-alpine sh -c \
  "npm install --global --silent @anthropic-ai/claude-code@$CLAUDE_CODE && claude plugin validate ./plugins/datumpin && claude plugin validate ."

exit "$FAILED"
