#!/usr/bin/env bash
# Decides whether a publish job uploads a package version from this branch.
# Each branch is a release channel of the one registry: `prep` publishes
# pre-releases, `main` publishes finals, and each skips the other kind. So a
# package releases when its own version says it is final, whatever the
# versions of the packages beside it in the same merge.
#
#   ci/release-channel.sh BRANCH VERSION   (DEVKIT; moved from PACKAGES scripts/ci/)
#
#   BRANCH   github.ref_name
#   VERSION  the version as published: the normalised PEP 440 version from the
#            built sdist (0.3.0rc1), or package.json's semver (0.3.0-rc.1)
#
# Writes publish=true|false and npm_tag=next|latest to $GITHUB_OUTPUT (stdout
# when that is unset). Fails on a version that is neither final nor a
# recognised pre-release, so a typo never publishes. Needs only bash.
set -euo pipefail

BRANCH="${1:?branch}"
VERSION="${2:?version}"

if [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  kind=final
elif [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+((a|b|rc)[0-9]+|\.dev[0-9]+|-[0-9A-Za-z.-]+)$ ]]; then
  kind=pre-release
else
  echo "Version '$VERSION' is neither final (1.2.3) nor a pre-release (1.2.3rc1, 1.2.3-rc.1)." >&2
  exit 1
fi

case "$BRANCH/$kind" in
  prep/pre-release | main/final) publish=true ;;
  *) publish=false ;;
esac
npm_tag=latest
[ "$kind" = pre-release ] && npm_tag=next

if [ "$publish" = true ]; then
  echo "$VERSION is a $kind; $BRANCH publishes it."
else
  echo "$VERSION is a $kind; $BRANCH does not publish it (prep publishes pre-releases, main finals)."
fi

out="${GITHUB_OUTPUT:-/dev/stdout}"
{
  echo "publish=$publish"
  echo "npm_tag=$npm_tag"
} >> "$out"
