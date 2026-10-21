"""An in-memory Gitea Board for testing ci/board_sync.py without a server.

Answers the calls board_sync makes through its one HTTP function, call(),
with Gitea's paging (at most `page_size` issues a page, 50 by default, as the
live server) and records every write. `ignores_page` serves page 1 for every
page, and `max_calls` stops a runaway loop, so a test fails instead of hanging.
"""
import re

COLUMNS = ["Triage", "Backlog", "In Progress", "Review", "Testing", "DoD", "Done"]
PAGE = 50


class FakeGitea:
    def __init__(self, page_size=PAGE, ignores_page=False, max_calls=500):
        self.page_size = page_size
        self.ignores_page = ignores_page
        self.max_calls = max_calls
        self.calls = 0
        self.board_id = 1
        self.column_ids = {title: 100 + i for i, title in enumerate(COLUMNS)}
        self.cards = {title: [] for title in COLUMNS}  # column -> issue numbers, in order
        self.writes = []

    def put(self, column, *numbers):
        self.cards[column].extend(numbers)

    def column_of(self, number):
        return next((t for t, nums in self.cards.items() if number in nums), None)

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
            limit = min(int(params.get("limit", self.page_size)), self.page_size)
            page = 1 if self.ignores_page else int(params.get("page", 1))
            numbers = self.cards[title][(page - 1) * limit:page * limit]
            return [{"id": 1000 + n, "number": n} for n in numbers]
        found = re.search(r"/issues/(\d+)$", path)
        if method == "GET" and found:
            number = int(found.group(1))
            return {"id": 1000 + number, "number": number}
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
            title = next(t for t, cid in self.column_ids.items() if cid == body["column_id"])
            self.cards[title].append(number)
            return None
        raise AssertionError(f"unexpected call: {method} {path}")
