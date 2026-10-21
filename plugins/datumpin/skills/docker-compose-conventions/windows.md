# Windows dev machine

Dev on Windows runs on plain Docker Desktop, with the checkouts on the Windows drive (decision in DEVKIT's roadmap; the move into WSL2 is DEVKIT #110). Parent: [SKILL.md](SKILL.md).

- **Line endings:** every repo's `.gitattributes` starts with `* text=auto eol=lf`, so the working copy has LF line endings, as the Linux containers, CI and the servers expect. A repo that adds the rule runs `git add --renormalize .` in the same PR.
- **Git Bash paths:** Git Bash rewrites arguments that look like Unix paths (`/w`, `/instance`) before `docker` sees them. Scripts that pass container paths set `export MSYS_NO_PATHCONV=1`; type it before such a command by hand.
- **Bind mounts:** a mount from the Windows drive is slower than on Linux, and file-change events do not reach the container. A dev server or test watcher that must notice edits polls (Vite: `server.watch.usePolling`).
- **Ports:** Docker Desktop publishes ports on the Windows side, out of reach of the daemon in its VM. A container the daemon itself must reach (a test registry) runs with `--network host` on the daemon's loopback.

## Done when

- `git ls-files --eol` shows no `w/crlf` for a text file after a fresh checkout.
- `ci/local-check.sh` (DEVKIT) and each repo's dev stack and tests run from Git Bash on the laptop.
