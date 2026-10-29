"""An in-memory Gitea for testing ci/board_sync.py and dp without a server.

Answers the calls both make through their one HTTP function, call(), with
Gitea's paging (at most `page_size` items a page, 50 by default, as the live
server) and records every write. `ignores_page` serves page 1 for every
page, and `max_calls` stops a runaway loop, so a test fails instead of hanging.
Issues, pull requests, milestones and labels are plain dicts in Gitea's
shape; an issue nobody added answers as its id and number alone.
"""
import re

COLUMNS = ["Triage", "Backlog", "In Progress", "Review", "Testing", "DoD", "Done"]
PAGE = 50


class FakeGitea:
    def __init__(self, page_size=PAGE, ignores_page=False, max_calls=500, lands_in=None):
        self.page_size = page_size
        self.ignores_page = ignores_page
        self.max_calls = max_calls
        self.lands_in = lands_in  # a move settles here, as a card board-sync moved on
        self.calls = 0
        self.board_id = 1
        self.column_ids = {title: 100 + i for i, title in enumerate(COLUMNS)}
        self.cards = {title: [] for title in COLUMNS}  # column -> issue numbers, in order
        self.issues = {}  # number -> issue
        self.comments = {}  # number -> comments, oldest first
        self.pulls = []
        self.milestones = []
        self.labels = {"repo": [], "org": []}
        self.writes = []

    def put(self, column, *numbers):
        self.cards[column].extend(numbers)

    def column_of(self, number):
        return next((t for t, nums in self.cards.items() if number in nums), None)

    def add_issue(self, number, title="", state="open", labels=(), milestone=None,
                  assignees=(), comments=()):
        """An issue, with its comments as (author, body) pairs."""
        self.comments[number] = [{"user": {"login": a}, "body": b} for a, b in comments]
        self.issues[number] = {
            "id": 1000 + number, "number": number, "title": title, "state": state,
            "labels": [{"name": name} for name in labels],
            "milestone": {"title": milestone} if milestone else None,
            "assignees": [{"login": login} for login in assignees] or None,
            "comments": len(comments)}

    def issue(self, number):
        return self.issues.get(number, {"id": 1000 + number, "number": number})

    def page(self, items, params):
        limit = min(int(params.get("limit", self.page_size)), self.page_size)
        page = 1 if self.ignores_page else int(params.get("page", 1))
        return items[(page - 1) * limit:page * limit]

    def call(self, method, path, body=None):
        self.calls += 1
        if self.calls > self.max_calls:
            raise AssertionError(f"more than {self.max_calls} calls: a runaway loop")
        path, _, query = path.partition("?")
        params = dict(p.split("=") for p in query.split("&") if p)
        if method == "GET" and path.endswith("/projects"):
            return [{"id": self.board_id, "title": "Board"}]
        if method == "GET" and path.endswith("/columns"):
            return [{"id": cid, "title": t} for t, cid in self.column_ids.items()]
        found = re.search(r"/columns/(\d+)/issues$", path)
        if method == "GET" and found:
            title = next(t for t, cid in self.column_ids.items() if cid == int(found.group(1)))
            return [self.issue(n) for n in self.page(self.cards[title], params)]
        if method == "GET" and re.search(r"^repos/[^/]+/[^/]+/issues$", path):
            state, milestone = params.get("state", "open"), params.get("milestones")
            wanted = [i for i in self.issues.values() if state in ("all", i["state"])
                      and (milestone is None or (i["milestone"] or {}).get("title") == milestone)]
            return self.page(wanted, params)
        found = re.search(r"/issues/(\d+)$", path)
        if method == "GET" and found:
            return self.issue(int(found.group(1)))
        if method == "PATCH" and found:
            number = int(found.group(1))
            if "milestone" in body:
                self.writes.append(("milestone", number, body["milestone"]))
                title = next(m["title"] for m in self.milestones if m["id"] == body["milestone"])
                self.issues[number]["milestone"] = {"title": title}
            if "state" in body:
                if body["state"] == "closed":
                    self.writes.append(("close", number))
                self.issues[number]["state"] = body["state"]
            if "assignees" in body:
                self.writes.append(("assign", number, body["assignees"]))
                self.issues[number]["assignees"] = [{"login": login} for login in body["assignees"]]
            return self.issues[number]
        found = re.search(r"/issues/(\d+)/comments$", path)
        if method == "GET" and found:
            return self.comments.get(int(found.group(1)), [])
        if method == "POST" and found:
            self.writes.append(("comment", int(found.group(1)), body["body"]))
            self.comments.setdefault(int(found.group(1)), []).append({"user": {"login": "MattM"}, "body": body["body"]})
            return {"id": 1, "body": body["body"]}
        if method == "GET" and path.endswith("/pulls"):
            return self.page(self.pulls, params)
        if method == "POST" and path.endswith("/pulls"):
            self.writes.append(("pull", body))
            return {"number": 900, "html_url": "http://gitea/Org/Repo/pulls/900"}
        if method == "GET" and path.endswith("/milestones"):
            return self.page(self.milestones, params)
        if method == "GET" and path.endswith("/labels"):
            return self.page(self.labels["org" if path.startswith("orgs/") else "repo"], params)
        found = re.search(r"/columns/(\d+)/issues/(\d+)$", path)
        if method == "POST" and found:
            self.writes.append(("add", int(found.group(2)) - 1000))
            title = next(t for t, cid in self.column_ids.items() if cid == int(found.group(1)))
            self.cards[title].append(int(found.group(2)) - 1000)
            return None
        found = re.search(r"/issues/(\d+)/move$", path)
        if method == "POST" and found:
            number = int(found.group(1)) - 1000
            self.writes.append(("move", number))
            for nums in self.cards.values():
                if number in nums:
                    nums.remove(number)
            title = self.lands_in or next(t for t, cid in self.column_ids.items() if cid == body["column_id"])
            self.cards[title].append(number)
            return None
        raise AssertionError(f"unexpected call: {method} {path}")
