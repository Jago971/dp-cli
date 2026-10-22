# Dependency versions

How a pinned version is checked and changed. Parent: [SKILL.md](SKILL.md).

## Dependency versions

Three checks, each covering what the others do not:

- **Known vulnerabilities, every PR, blocking:** osv-scanner in DEVKIT's `security-scan`.
- **Approved versions, every PR, blocking:** the `versions` job fails when a listed package is pinned to another version than the master copies in DEVKIT `ci/master/` (`DRIFT` minor or patch, `MAJOR` major). Unlisted packages are counted, and osv-scanner covers them until they are listed.
- **What ships, on image build:** the image's CycloneDX SBOM goes to OWASP Dependency-Track when the org variable `DEPENDENCY_TRACK_URL` is set.

A master copy changes only through a DEVKIT PR: the new version is reviewed in Dependency-Track first, and an Owner approves the PR. The repos then conform: master first, never a repo-only upgrade of a listed package.
