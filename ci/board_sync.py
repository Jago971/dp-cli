"""Moves tickets across a repo's Gitea Board as their pull requests progress.

Run by DEVKIT's board-sync workflow on pull request and issue events. The
column is the ticket's state (the gitea skill); this keeps it true without
anyone dragging cards:

    pull request opened or reopened -> each ticket it names: Review
    pull request merged into prep   -> each ticket it names: Testing
    issue opened                    -> Triage, when not on the Board yet
    issue closed                    -> DoD, where it waits for the release gate
    pull request merged prep -> main -> the milestone it carries: DoD tickets to Done, with a comment
    issue reopened                  -> Backlog

A release leaves a ticket not in DoD where it is and lists it in the log.

A pull request names a ticket with "Refs #N" (the formats skill) or through
its branch, <type>/<N>-<slug>. A ticket it only relates to goes on a "See #N"
line and is not moved. A ticket already further along (DoD, Done) is
never moved back by a pull request event. Another repo's tickets
(Owner/Repo#N) are left alone. A ticket not on the Board is placed on it.

Reads the event from GITHUB_EVENT_PATH and calls the Gitea API at API_URL for
REPOSITORY with TOKEN. Standard library only.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

ORDER = ["Triage", "Backlog", "In Progress", "Review", "Testing", "DoD", "Done"]
MAX_PAGES = 40  # 2,000 tickets a column at 50 a page


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
    for line in re.findall(r"(?im)^[ \t]*Refs\b.*$", text):
        numbers |= {int(n) for n in re.findall(r"(?<![\w/])#(\d+)", line)}
    branch = re.match(r"^[a-z]+/(\d+)-", pull.get("head", {}).get("ref", ""))
    if branch:
        numbers.add(int(branch.group(1)))
    numbers.discard(pull.get("number"))
    return sorted(numbers)


def column_holding(repo, board_id, columns, issue_id):
    """The title of the column holding the issue, or None when it is not on the Board.

    Gitea caps a page at its MAX_RESPONSE_ITEMS (50 by default), so each column
    is read until an empty page. A server that ignored `page` would never send
    one; MAX_PAGES stops that instead of looping until the job times out.
    """
    for title, cid in columns.items():
        for page in range(1, MAX_PAGES + 1):
            issues = call("GET", f"repos/{repo}/projects/{board_id}/columns/{cid}/issues?limit=50&page={page}")
            if not issues:
                break
            if any(i["id"] == issue_id for i in issues):
                return title
        else:
            raise RuntimeError(f"{title}: no empty page after {MAX_PAGES} pages; is paging honoured?")
    return None


def board_of(repo):
    """The repo's open Board and its columns as (board, {title: id}), or None without a Board."""
    board = next((p for p in call("GET", f"repos/{repo}/projects?state=open") if p["title"] == "Board"), None)
    if board is None:
        return None
    return board, {c["title"]: c["id"] for c in call("GET", f"repos/{repo}/projects/{board['id']}/columns")}


def move(repo, number, column, forward_only):
    found = board_of(repo)
    if found is None:
        print(f"SKIP  #{number}: {repo} has no Board")
        return
    board, columns = found
    issue = call("GET", f"repos/{repo}/issues/{number}")
    if issue.get("pull_request"):
        return
    current = column_holding(repo, board["id"], columns, issue["id"])
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


def release(repo, pull):
    """Moves the DoD tickets of the pull request's milestone to Done, commenting the release."""
    milestone = (pull.get("milestone") or {}).get("title")
    if not milestone:
        print("SKIP  release pull request has no milestone")
        return
    found = board_of(repo)
    if found is None:
        print(f"SKIP  {repo} has no Board")
        return
    board, columns = found
    query = f"state=all&type=issues&milestones={urllib.parse.quote(milestone)}&limit=50"
    for page in range(1, MAX_PAGES + 1):
        issues = call("GET", f"repos/{repo}/issues?{query}&page={page}")
        if not issues:
            return
        for issue in issues:
            current = column_holding(repo, board["id"], columns, issue["id"])
            if current != "DoD":
                print(f"LEAVE #{issue['number']}: in {current or 'not on the Board'}, not DoD")
                continue
            move(repo, issue["number"], "Done", forward_only=True)
            call("POST", f"repos/{repo}/issues/{issue['number']}/comments",
                 {"body": f"Released in {milestone} (#{pull['number']})."})
    raise RuntimeError(f"{milestone}: no empty page after {MAX_PAGES} pages; is paging honoured?")


def main():
    repo = os.environ["REPOSITORY"]
    event = json.load(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8"))
    action = event.get("action")
    if "pull_request" in event:
        pull = event["pull_request"]
        merged = action == "closed" and pull.get("merged")
        if merged and pull.get("base", {}).get("ref") == "main" and pull.get("head", {}).get("ref") == "prep":
            release(repo, pull)
            return
        if action in ("opened", "reopened", "ready_for_review"):
            target = "Review"
        elif merged and pull.get("base", {}).get("ref") == "prep":
            target = "Testing"
        else:
            print(f"SKIP  pull request {action}: nothing to move")
            return
        for number in tickets_named(pull):
            move(repo, number, target, forward_only=True)
    elif "issue" in event and not event["issue"].get("pull_request"):
        # forward_only on opened: shape may already have placed the ticket further on
        target, forward_only = {"opened": ("Triage", True), "closed": ("DoD", True),
                                "reopened": ("Backlog", False)}.get(action, (None, False))
        if target:
            move(repo, event["issue"]["number"], target, forward_only)
    else:
        print("SKIP  not a pull request or issue event")


if __name__ == "__main__":
    sys.exit(main())
