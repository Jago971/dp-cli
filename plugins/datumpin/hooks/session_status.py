"""Session-start status line for the datumpin workflow.

Prints one line into the new session: this repo's Triage count and open PRs
on its Gitea Board, and DEVKIT's Triage count, so parked tickets and
plugin or CI findings are seen without anyone remembering to look. Reads
Gitea through `tea` as the agent login. Prints nothing, and exits 0, when
the repo is not a Datumpin Gitea repo or Gitea or `tea` is unavailable:
a status line must never get in the way of a session.
"""
import json
import os
import re
import subprocess

OWNER = "Datumpin"
DEVKIT = f"{OWNER}/DEVKIT"
TIMEOUT = 8  # seconds per call; the hook itself is capped in hooks.json


def run(*args, cwd=None):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                            encoding="utf-8", timeout=TIMEOUT, check=True)
    return result.stdout


def repo_slug(project_dir):
    url = run("git", "remote", "get-url", "origin", cwd=project_dir).strip()
    match = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?$", url)
    return match.group(1) if match else None


def agent_login(project_dir):
    flow = os.path.join(project_dir, ".claude", "flow.yaml")
    if os.path.exists(flow):
        match = re.search(r"^\s*agent_login:\s*(\S+)", open(flow, encoding="utf-8").read(), re.M)
        if match:
            return match.group(1)
    return "squire"


def api(login, endpoint):
    return json.loads(run("tea", "api", "--login", login, endpoint))


def triage_count(login, slug):
    boards = [p for p in api(login, f"repos/{slug}/projects?state=open") if p["title"] == "Board"]
    if not boards:
        return None
    columns = api(login, f"repos/{slug}/projects/{boards[0]['id']}/columns")
    triage = [c for c in columns if c["title"] == "Triage"]
    if not triage:
        return None
    issues = api(login, f"repos/{slug}/projects/{boards[0]['id']}/columns/{triage[0]['id']}/issues?limit=50")
    return sum(1 for issue in issues if issue.get("state", "open") == "open")


def main():
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    slug = repo_slug(project_dir)
    if not slug or not slug.startswith(OWNER + "/"):
        return
    login = agent_login(project_dir)
    parts = []
    triage = triage_count(login, slug)
    prs = len(api(login, f"repos/{slug}/pulls?state=open&limit=50"))
    parts.append(f"{slug}: Triage {triage if triage is not None else '-'}, open PRs {prs}")
    if slug.lower() != DEVKIT.lower():
        parts.append(f"{DEVKIT}: Triage {triage_count(login, DEVKIT)}")
    print("datumpin status | " + " | ".join(parts)
          + ". If Triage is not empty, offer the user a short sort (/datumpin:board).")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
