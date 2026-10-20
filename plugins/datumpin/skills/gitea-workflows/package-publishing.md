# Publishing workflows for a package monorepo

PACKAGES' test and publish workflows. Parent: [SKILL.md](SKILL.md).

- **One job per changed package.** A first `detect` job (checkout with `fetch-depth: 0`) outputs one boolean per package (hyphens become underscores: `table-view` is `table_view`). Each package has its own explicit, named job with `needs: detect` and `if: needs.detect.outputs.<pkg> == 'true'`. Keep the logic in one script (package table in, booleans out, `git` and `bash` only) so it runs locally against real history.
  - The base is the push's `before` or the PR's base sha.
  - An all-zero or unknown base, `workflow_dispatch`, or a change to the workflow file selects every package.
- **Each package job calls DEVKIT's `publish-python` or `publish-npm`** (`package-dir`, and `siblings` for a package built against its siblings), mapping the repo's write secrets to `PKG_USER` and `PKG_WRITE_TOKEN`. List the jobs one per package: the runner did not expand matrices from `needs` outputs (`matrix.include: ${{ fromJSON(needs.detect.outputs.x) }}` ran one job with `${{ matrix.package }}` unresolved), and YAML anchors are not supported.
- **Make publishing idempotent.** Gitea's PyPI registry does not support `twine upload --skip-existing`. Upload each file on its own and treat `409 Conflict` as already published. For npm, check `npm view` for the version first.
- **A version-parity test fails the job** when a package's metadata and `__init__` disagree.
- **Add `workflow_dispatch`.** A push trigger sees only its `paths:` filter, so a change to the workflow file alone starts nothing. "Run workflow" treats every package as changed.
- **Write the npm token to a temporary user-level config** (`NPM_CONFIG_USERCONFIG` from `mktemp`, removed on exit), because npm ignores a workspace member's own `.npmrc` (`ENEEDAUTH` otherwise).
- **Each branch is a release channel of the one registry.** A push to `prep` publishes a changed package whose version is a pre-release (PEP 440 `0.3.0rc1`, semver `0.3.0-rc.1` under the npm `next` tag); a push to `main` publishes one whose version is final. Each skips the other kind, so a package releases when its own version is final, whatever its neighbours' versions in the same merge. One script decides from the branch and the version as published (the normalised sdist version, or `package.json`) and rejects anything else; every job calls it. Feature branches publish nothing.
- **Promote the package before its consumer.** Bump to a pre-release and merge to `prep`; the consumer's `prep` pins it and tries it. Then bump to the final version, merge to `prep`, and promote `prep` to `main`, which publishes the final. The consumer pins the final on its `prep` before its own promotion. A consumer's `main` never pins a pre-release.
- **Expected behaviour of a correct setup:** a PR touching only `packages/identity` runs tests for `identity` and its dependants and skips the rest. Its merge runs only the `identity` publish job, which publishes when the version suits the branch and answers 409 when the version is unchanged. A change outside `packages/**` starts no publish.

## Done when

- `actionlint` and `shellcheck` are clean on the workflow files (the `rhysd/actionlint` image carries both).
- A manual `workflow_dispatch` ends with every upload answering 409 and nothing new published.
- A PR touching one package starts only that package's jobs and its dependants'.
