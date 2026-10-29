"""dp's commands: each one Gitea task in one call, returning plain data.

Summary: board, move, pr and pointer, as the gitea skill describes each task,
         and the reads `dp guide` needs: the columns and one ticket in full.
Input:   call(method, path, body=None) from dp.gitea (a fake in tests) and the
         repo slug.
Output:  dicts and lists the command line prints as text or JSON; GiteaError
         when the repo, a column or a label is missing, or text breaks a shape.
"""
import re
from concurrent.futures import ThreadPoolExecutor

from dp.gitea import GiteaError

WORKERS = 8  # calls at once: each is a tea process and a round trip of about 0.6 s
PAGE = 50
MAX_PAGES = 40  # 2,000 items at 50 a page; a server ignoring `page` stops here
# The formats skill's Pointer: <Event>, <YYYY-MM-DD>. <Verdict>: <one line>. → <ref>
POINTER = re.compile(r"[^\n,]+, \d{4}-\d{2}-\d{2}\. "
                     r"(Covered|Carried forward|Obsolete|Duplicate|Done): [^\n]+\. → \S[^\n]*")


def paged(call, path):
    """Every item of a listing, read until an empty page."""
    items = []
    joiner = "&" if "?" in path else "?"
    for page in range(1, MAX_PAGES + 1):
        batch = call("GET", f"{path}{joiner}limit={PAGE}&page={page}")
        if not batch:
            return items
        items.extend(batch)
    raise GiteaError(f"{path}: more than {MAX_PAGES} pages; is the server ignoring page?")


def find_board(call, repo):
    """The Board's id and its columns, title to id, in board order."""
    board = next((p for p in call("GET", f"repos/{repo}/projects?state=open")
                  if p["title"] == "Board"), None)
    if not board:
        raise GiteaError(f"{repo} has no project titled Board (run align)")
    columns = call("GET", f"repos/{repo}/projects/{board['id']}/columns")
    return board["id"], {column["title"]: column["id"] for column in columns}


def each(work, items):
    """work(item) for every item, several at once, results in item order."""
    with ThreadPoolExecutor(WORKERS) as pool:
        return list(pool.map(work, items))


def column_issues(call, repo, board_id, columns):
    """Each column's title and its issues, every page, in board order."""
    issues = each(lambda column_id: paged(
        call, f"repos/{repo}/projects/{board_id}/columns/{column_id}/issues"), columns.values())
    return dict(zip(columns, issues))


def ticket(issue):
    return {"number": issue["number"], "title": issue.get("title", ""),
            "state": issue.get("state", "open"),
            "labels": [label["name"] for label in issue.get("labels") or []],
            "milestone": (issue.get("milestone") or {}).get("title"),
            "assignees": [user["login"] for user in issue.get("assignees") or []]}


def last_comment(call, repo, issue):
    """The author and text of an open issue's last comment, or None."""
    if issue.get("state") != "open" or not issue.get("comments"):
        return None
    comments = call("GET", f"repos/{repo}/issues/{issue['number']}/comments")
    return {"author": comments[-1]["user"]["login"], "text": comments[-1]["body"]} if comments else None


def column_tickets(call, repo):
    """Each Board column's title and its tickets, in board order."""
    board_id, ids = find_board(call, repo)
    return {title: [ticket(issue) for issue in issues]
            for title, issues in column_issues(call, repo, board_id, ids).items()}


def issue(call, repo, number):
    """Ticket N with its body and its comments, oldest first."""
    found, comments = each(lambda path: call("GET", path),
                           [f"repos/{repo}/issues/{number}", f"repos/{repo}/issues/{number}/comments"])
    return {**ticket(found), "body": found.get("body") or "",
            "comments": [{"author": c["user"]["login"], "text": c["body"]} for c in comments or []]}


def board(call, repo):
    """The Board's columns with their tickets, open issues off it, open PRs and milestones."""
    board_id, columns = find_board(call, repo)
    listings = [f"repos/{repo}/projects/{board_id}/columns/{column_id}/issues"
                for column_id in columns.values()]
    listings += [f"repos/{repo}/issues?state=open&type=issues", f"repos/{repo}/pulls?state=open",
                 f"repos/{repo}/milestones?state=open"]
    *in_columns, open_issues, open_pulls, open_milestones = each(lambda path: paged(call, path), listings)
    placed = dict(zip(columns, in_columns))
    on_board = {issue["number"] for issues in in_columns for issue in issues}
    off_board = [issue for issue in open_issues if issue["number"] not in on_board]
    everything = [issue for issues in in_columns for issue in issues] + off_board
    comments = dict(zip((issue["number"] for issue in everything),
                        each(lambda issue: last_comment(call, repo, issue), everything)))

    def tickets(issues):
        return [{**ticket(issue), "last_comment": comments[issue["number"]]} for issue in issues]

    return {
        "repo": repo,
        "columns": [{"title": title, "tickets": tickets(issues)} for title, issues in placed.items()],
        "unsorted": tickets(off_board),
        "pulls": [{"number": p["number"], "title": p["title"], "head": p["head"]["ref"],
                   "base": p["base"]["ref"], "labels": [label["name"] for label in p.get("labels") or []]}
                  for p in open_pulls],
        "milestones": [{"title": m["title"], "open": m["open_issues"], "closed": m["closed_issues"]}
                       for m in open_milestones]}


def move(call, repo, number, column, assignee=None):
    """Put ticket N in a column (placing it on the Board if needed); assign on In Progress."""
    board_id, columns = find_board(call, repo)
    title = next((t for t in columns if t.lower() == column.lower()), None)
    if title is None:
        raise GiteaError(f"no column {column!r}; columns: {', '.join(columns)}")
    issue = call("GET", f"repos/{repo}/issues/{number}")
    current = next((t for t, issues in column_issues(call, repo, board_id, columns).items()
                    if any(i["id"] == issue["id"] for i in issues)), None)
    if current is None:
        call("POST", f"repos/{repo}/projects/{board_id}/columns/{columns[title]}/issues/{issue['id']}")
    elif current != title:
        call("POST", f"repos/{repo}/projects/{board_id}/issues/{issue['id']}/move",
             {"column_id": columns[title]})
    assigned = None
    if title == "In Progress" and assignee:
        existing = [user["login"] for user in issue.get("assignees") or []]
        if assignee not in existing:
            call("PATCH", f"repos/{repo}/issues/{number}", {"assignees": existing + [assignee]})
        assigned = assignee
    return {"number": number, "from": current, "to": title, "assigned": assigned}


def earliest_milestone(call, repo):
    """The open milestone due first (the oldest when none is due), or None."""
    open_milestones = paged(call, f"repos/{repo}/milestones?state=open")
    return min(open_milestones, key=lambda m: (m.get("due_on") is None, m.get("due_on") or "", m["id"]),
               default=None)


def join_earliest_milestone(call, repo, number):
    """Put ticket N in the open milestone due first (the oldest when none is due); its title, or None."""
    earliest = earliest_milestone(call, repo)
    if not earliest:
        return None
    call("PATCH", f"repos/{repo}/issues/{number}", {"milestone": earliest["id"]})
    return earliest["title"]


def pr(call, repo, head, base, title, body, labels):
    """Open a pull request; labels are names, from the repo's labels or its org's."""
    org = repo.split("/")[0]
    ids = {label["name"]: label["id"]
           for path in (f"orgs/{org}/labels", f"repos/{repo}/labels") for label in paged(call, path)}
    missing = [name for name in labels if name not in ids]
    if missing:
        raise GiteaError(f"no label {', '.join(missing)} in {repo} or {org}")
    pull = call("POST", f"repos/{repo}/pulls", {"head": head, "base": base, "title": title,
                                                "body": body, "labels": [ids[name] for name in labels]})
    return {"number": pull["number"], "url": pull["html_url"]}


def finish(call, repo, number):
    """Close ticket N, put it in DoD, and return the column it is in."""
    call("PATCH", f"repos/{repo}/issues/{number}", {"state": "closed"})
    move(call, repo, number, "DoD")
    board_id, columns = find_board(call, repo)
    held = column_issues(call, repo, board_id, columns)
    return next((title for title, issues in held.items() if any(i["number"] == number for i in issues)), None)


def reopen(call, repo, number, text):
    """Reopen ticket N to Backlog with a Progress comment."""
    call("POST", f"repos/{repo}/issues/{number}/comments", {"body": text})
    call("PATCH", f"repos/{repo}/issues/{number}", {"state": "open"})
    move(call, repo, number, "Backlog")


def pointer(call, repo, number, text):
    """Post a Pointer comment on ticket N, refusing text outside the Pointer shape."""
    if not POINTER.fullmatch(text):
        raise GiteaError("not a Pointer: <Event>, <YYYY-MM-DD>. <Verdict>: <one line>. → <#N | path>"
                         " (Verdict: Covered, Carried forward, Obsolete, Duplicate or Done)")
    call("POST", f"repos/{repo}/issues/{number}/comments", {"body": text})
    return {"number": number, "text": text}
