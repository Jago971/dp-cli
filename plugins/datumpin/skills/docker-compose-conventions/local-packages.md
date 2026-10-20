# Local-packages override

For a dev machine whose Docker cannot reach the private registry while the host can (the owner's laptop: the host reaches Gitea through a route Docker containers cannot use). Parent: [SKILL.md](SKILL.md).

The normal build installs private packages from the registry, with the token passed as a BuildKit secret (`secrets-handling`). Every repo that installs private packages (AHJV2, CURATOR, BDS) carries the override in the same two files: `docker-compose.local-packages.yml` and `Dockerfile*.local-packages`. Those files are the worked example.

## How it works

- Docker's additional build context (`build.additional_contexts` in compose, `--mount=type=bind,from=<name>` in the Dockerfile) takes each package's source from the sibling `../PACKAGES` checkout, so no registry is involved.
- It is a dependency bump, not a live edit. Rebuild the image to pick up a change to the sibling source.
- Layer it with a second `-f` flag on top of the dev compose file. The shared `Dockerfile.dev` and `docker-compose.dev.yml` keep the registry install, because every other host (deploy server, CI) pulls those files and has no `../PACKAGES`.
- Put the install logic in one script in the sibling repo, per package manager. Each Dockerfile `COPY --from=<scripts-context>`s it and calls it with the package name and path.
- Packages that depend on each other install in one call, dependencies first, through the multi-package scripts (`dev-install-pip-many.sh <requirements-file> <pip-name>=<dir> ...`, `dev-install-npm-many.js <@scope/name>=<dir> ...`). The `datumpin-*` lines drop out of the image-local requirements, the rest installs from the public index, then each source directory installs in order. A pin at a version the registry does not carry yet works only through this override.
- Set `BUILDX_BAKE_ENTITLEMENTS_FS=0` on the laptop, or buildx refuses filesystem access to the sibling checkout.

## Two build gotchas

- A `setup.py` package writes build artifacts (`pdv.egg-info`) into its source directory, which fails on a read-only mount. Mount it `,rw`. The additional context is a snapshot BuildKit took for this build, so writes stay in the build layer.
- BuildKit's context uploader fails on the symlinks inside a pre-built `node_modules` (`node_modules/.bin/...`). Put `node_modules` in a `.dockerignore` in the sibling package's directory, and have the consumer merge that package's `dependencies` into its own manifest so the public registry resolves them.

## Done when

- A rebuild with both `-f` files succeeds on the laptop, and the plain dev compose file still builds unmodified on a registry-connected host.
- `docker exec <container> pip show <package>` (or `npm ls`) reports the local source version.
