"""The one way dp reaches Gitea: `tea api`, as one of tea's logins.

Summary: call(method, path, body) for a tea login, and who the repo and its
         logins are.
Input:   tea's logins (`tea logins list`), the repo's git remote and its
         `.claude/flow.yaml`.
Output:  parsed JSON replies; GiteaError for an HTTP error, a failed tea or an
         unreachable server.

`tea api` exits 0 on an HTTP error, so the status is read from the headers
`--include` writes to stderr.
"""
import json
import re
import subprocess
from pathlib import Path

AGENT_LOGIN = "squire"  # the plugin default, gitea.agent_login in defaults/flow.yaml
TIMEOUT = 30  # seconds per call
STATUS = re.compile(r"^HTTP/\S+ (\d{3})", re.M)


class GiteaError(Exception):
    """A Gitea call failed, or Gitea or tea is unavailable."""


def run(*args, stdin=None, cwd=None):
    """A command's result, or GiteaError when it cannot start or times out."""
    try:
        return subprocess.run(list(args), input=stdin, cwd=cwd, capture_output=True, text=True,
                              encoding="utf-8", timeout=TIMEOUT)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise GiteaError(f"{args[0]} failed: {error}") from error


def tea(login):
    """A call(method, path, body=None) that runs `tea api` as `login`."""
    def call(method, path, body=None):
        args = ["tea", "api", "--include", "--login", login, "-X", method, path]
        if body is not None:
            args += ["--data", "@-"]
        result = run(*args, stdin=json.dumps(body) if body is not None else None)
        status = STATUS.search(result.stderr)
        if result.returncode or not status:
            lines = result.stderr.strip().splitlines()
            raise GiteaError(lines[-1] if lines else f"tea exited {result.returncode}")
        if int(status.group(1)) >= 400:
            raise GiteaError(f"{method} {path}: HTTP {status.group(1)} {result.stdout.strip()}")
        return json.loads(result.stdout) if result.stdout.strip() else None
    return call


def repo_slug(remote_url):
    """Owner/Repo from a git remote URL."""
    match = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?/?$", remote_url.strip())
    if not match:
        raise GiteaError(f"no Owner/Repo in the remote {remote_url!r}")
    return match.group(1)


def agent_login(root):
    """The agent's tea login: the repo's `gitea.agent_login`, else the plugin default."""
    flow = Path(root) / ".claude" / "flow.yaml"
    if flow.is_file():
        match = re.search(r"^\s*agent_login:\s*(\S+)", flow.read_text(encoding="utf-8"), re.M)
        if match:
            return match.group(1)
    return AGENT_LOGIN


def logins():
    """tea's logins, as `tea logins list --output json` gives them."""
    result = run("tea", "logins", "list", "--output", "json")
    if result.returncode:
        raise GiteaError(f"tea logins list failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def human_username(all_logins, agent):
    """The Gitea username of the one tea login that is not the agent's."""
    humans = [login for login in all_logins if login["name"] != agent]
    if len(humans) != 1:
        names = ", ".join(login["name"] for login in humans) or "none"
        raise GiteaError(f"need exactly one human tea login besides {agent}; found: {names}")
    return humans[0]["user"]
