"""Moves tickets across a repo's Gitea Board as their pull requests progress.

Run by DEVKIT's board-sync workflow on pull request and issue events. The
column is the ticket's state (the gitea skill); this keeps it true without
anyone dragging cards:

    pull request opened or reopened -> each ticket it names: Review
    pull request merged into prep   -> each ticket it names: Testing
    issue closed                    -> Done
    issue reopened                  -> Backlog

A pull request names a ticket with "Refs #N" (the formats skill) or through
its branch, <type>/<N>-<slug>. A ticket already further along (DoD, Done) is
never moved back by a pull request event. Another repo's tickets
(Owner/Repo#N) are left alone. A ticket not on the Board is placed on it.

Reads the event from GITHUB_EVENT_PATH and calls the Gitea API at API_URL for
REPOSITORY with TOKEN. Standard library only.
"""
import json
import os
import re
import sys
import urllib.request

ORDER = ["Triage", "Backlog", "In Progress", "Review", "Testing", "DoD", "Done"]


def call(method, path, body=None):
    request = urllib.request.Request(
        f"{os.environ['API_URL']}/{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"token {os.environ['TOKEN']}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        text = response.read().decode()
    return json.loads(text) if text.strip() else None


def tickets_named(pull):
    text = f"{pull.get('title', '')}\n{pull.get('body') or ''}"
    numbers = set()
    for line in re.findall(r"(?im)^\s*Refs\b.*$", text):
        numbers |= {int(n) for n in re.findall(r"(?<![\w/])#(\d+)", line)}
    branch = re.match(r"^[a-z]+/(\d+)-", pull.get("head", {}).get("ref", ""))
    if branch:
        numbers.add(int(branch.group(1)))
    numbers.discard(pull.get("number"))
    return sorted(numbers)


def move(repo, number, column, forward_only):
    board = next((p for p in call("GET", f"repos/{repo}/projects?state=open") if p["title"] == "Board"), None)
    if board is None:
        print(f"SKIP  #{number}: {repo} has no Board")
        return
    columns = {c["title"]: c["id"] for c in call("GET", f"repos/{repo}/projects/{board['id']}/columns")}
    issue = call("GET", f"repos/{repo}/issues/{number}")
    if issue.get("pull_request"):
        return
    current = next((title for title, cid in columns.items()
                    if any(i["id"] == issue["id"] for i in
                           call("GET", f"repos/{repo}/projects/{board['id']}/columns/{cid}/issues?limit=50"))), None)
    if current == column:
        print(f"KEEP  #{number}: already in {column}")
        return
    if forward_only and current in ORDER and ORDER.index(current) > ORDER.index(column):
        print(f"KEEP  #{number}: in {current}, past {column}")
        return
    if current is None:
        call("POST", f"repos/{repo}/projects/{board['id']}/columns/{columns[column]}/issues/{issue['id']}")
    else:
        call("POST", f"repos/{repo}/projects/{board['id']}/issues/{issue['id']}/move", {"column_id": columns[column]})
    print(f"MOVE  #{number}: {current or 'not on the Board'} -> {column}")


def main():
    repo = os.environ["REPOSITORY"]
    event = json.load(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8"))
    action = event.get("action")
    if "pull_request" in event:
        pull = event["pull_request"]
        if action in ("opened", "reopened", "ready_for_review"):
            target = "Review"
        elif action == "closed" and pull.get("merged") and pull.get("base", {}).get("ref") == "prep":
            target = "Testing"
        else:
            print(f"SKIP  pull request {action}: nothing to move")
            return
        for number in tickets_named(pull):
            move(repo, number, target, forward_only=True)
    elif "issue" in event and not event["issue"].get("pull_request"):
        target = {"closed": "Done", "reopened": "Backlog"}.get(action)
        if target:
            move(repo, event["issue"]["number"], target, forward_only=False)
    else:
        print("SKIP  not a pull request or issue event")


if __name__ == "__main__":
    sys.exit(main())
