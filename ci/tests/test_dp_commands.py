"""Unit tier: dp's commands (plugins/datumpin/dp) against the in-memory Gitea."""
import pytest

from dp import commands
from dp.gitea import GiteaError
from fake_gitea import FakeGitea

REPO = "Org/Repo"


@pytest.fixture
def gitea():
    return FakeGitea()


def numbers(tickets):
    return [ticket["number"] for ticket in tickets]


@pytest.mark.unit
def test_board_lists_every_page_of_every_column():
    gitea = FakeGitea(page_size=2)
    for n in range(1, 6):
        gitea.add_issue(n, title=f"Ticket {n}")
    gitea.put("Backlog", 1, 2, 3, 4, 5)

    board = commands.board(gitea.call, REPO)

    backlog = next(column for column in board["columns"] if column["title"] == "Backlog")
    assert numbers(backlog["tickets"]) == [1, 2, 3, 4, 5]


@pytest.mark.unit
def test_board_puts_open_issues_off_the_board_in_unsorted(gitea):
    gitea.add_issue(1, labels=["TYPE/BUG"], milestone="v1.0.0")
    gitea.add_issue(2)
    gitea.put("Triage", 1)

    board = commands.board(gitea.call, REPO)

    assert numbers(board["unsorted"]) == [2]
    triage = board["columns"][0]
    assert triage["tickets"][0]["labels"] == ["TYPE/BUG"]
    assert triage["tickets"][0]["milestone"] == "v1.0.0"


@pytest.mark.unit
def test_board_gives_each_open_ticket_its_last_comment(gitea):
    gitea.add_issue(1, comments=[("MattM", "first"), ("Squire", "Done, 2026-10-21. Done: shipped. → #9")])
    gitea.add_issue(2)
    gitea.put("Done", 1, 2)

    tickets = commands.board(gitea.call, REPO)["columns"][-1]["tickets"]

    assert tickets[0]["last_comment"] == {"author": "Squire", "text": "Done, 2026-10-21. Done: shipped. → #9"}
    assert tickets[1]["last_comment"] is None


@pytest.mark.unit
def test_board_lists_open_pulls_and_milestone_counts(gitea):
    gitea.pulls.append({"number": 7, "title": "Fix", "head": {"ref": "fix/3-x"},
                        "base": {"ref": "prep"}, "labels": [{"name": "TYPE/BUG"}]})
    gitea.milestones.append({"title": "v1.0.0 – First", "open_issues": 2, "closed_issues": 3})

    board = commands.board(gitea.call, REPO)

    assert board["pulls"] == [{"number": 7, "title": "Fix", "head": "fix/3-x", "base": "prep",
                               "labels": ["TYPE/BUG"]}]
    assert board["milestones"] == [{"title": "v1.0.0 – First", "open": 2, "closed": 3}]


@pytest.mark.unit
def test_move_to_in_progress_assigns_the_human(gitea):
    gitea.add_issue(4, assignees=["Other"])
    gitea.put("Backlog", 4)

    moved = commands.move(gitea.call, REPO, 4, "in progress", assignee="MattM")

    assert gitea.column_of(4) == "In Progress"
    assert ("assign", 4, ["Other", "MattM"]) in gitea.writes
    assert moved == {"number": 4, "from": "Backlog", "to": "In Progress", "assigned": "MattM"}


@pytest.mark.unit
def test_move_elsewhere_assigns_nobody_and_places_a_ticket_off_the_board(gitea):
    gitea.add_issue(4)

    moved = commands.move(gitea.call, REPO, 4, "Backlog", assignee="MattM")

    assert gitea.column_of(4) == "Backlog"
    assert gitea.writes == [("add", 4)]
    assert moved["from"] is None and moved["assigned"] is None


@pytest.mark.unit
def test_move_to_an_unknown_column_names_the_columns(gitea):
    gitea.add_issue(4)

    with pytest.raises(GiteaError, match="Triage, Backlog"):
        commands.move(gitea.call, REPO, 4, "Doing")


@pytest.mark.unit
def test_pr_opens_with_label_ids_from_repo_and_org(gitea):
    gitea.labels["repo"].append({"id": 5, "name": "COMPONENT/API"})
    gitea.labels["org"].append({"id": 9, "name": "TYPE/FEATURE"})

    opened = commands.pr(gitea.call, REPO, "feat/4-x", "prep", "Title", "Body",
                         ["TYPE/FEATURE", "COMPONENT/API"])

    assert gitea.writes == [("pull", {"head": "feat/4-x", "base": "prep", "title": "Title",
                                      "body": "Body", "labels": [9, 5]})]
    assert opened == {"number": 900, "url": "http://gitea/Org/Repo/pulls/900"}


@pytest.mark.unit
def test_pr_copies_the_tickets_labels_and_milestone(gitea):
    gitea.labels["org"].append({"id": 9, "name": "TYPE/FEATURE"})
    gitea.add_issue(4, labels=["TYPE/FEATURE"], milestone="v1")

    commands.pr(gitea.call, REPO, "feat/4-x", "prep", "Title", "Body", [], ticket=4)

    assert gitea.writes == [("pull", {"head": "feat/4-x", "base": "prep", "title": "Title",
                                      "body": "Body", "labels": [9], "milestone": 7})]


@pytest.mark.unit
def test_pr_with_an_unknown_label_writes_nothing(gitea):
    with pytest.raises(GiteaError, match="TYPE/NOPE"):
        commands.pr(gitea.call, REPO, "feat/4-x", "prep", "Title", "Body", ["TYPE/NOPE"])

    assert gitea.writes == []


@pytest.mark.unit
def test_pointer_posts_a_comment_in_the_pointer_shape(gitea):
    text = "Backlog reset, 2026-10-20. Carried forward: datetime convention. → #78"

    commands.pointer(gitea.call, REPO, 12, text)

    assert gitea.writes == [("comment", 12, text)]


@pytest.mark.unit
def test_pointer_refuses_text_outside_the_pointer_shape(gitea):
    with pytest.raises(GiteaError, match="Pointer"):
        commands.pointer(gitea.call, REPO, 12, "Closing this one.")

    assert gitea.writes == []


@pytest.mark.unit
def test_pr_body_fills_the_formats_shape():
    body = commands.pr_body(
        summary="dp fills the fixed PR text.",
        changes=[("plugins/datumpin/dp", "pr_body builder")],
        evidence="12 passed",
        findings=[("S1", "Name is vague", "low", "Fixed (abc1234)")],
        refs=["#122"], see=["#121"], check=["Read the body once"])

    assert body == (
        "## Summary\ndp fills the fixed PR text.\n\n"
        "## Changes\n- `plugins/datumpin/dp`: pr_body builder\n\n"
        "## Review\nEvidence: 12 passed\n\n"
        "| # | Finding | Sev | Disposition |\n|---|---|---|---|\n"
        "| S1 | Name is vague | low | Fixed (abc1234) |\n\n"
        "## Refs\nRefs #122\nSee #121\n\n"
        "## Check before merging\n- Read the body once\n")


@pytest.mark.unit
def test_pr_body_omits_empty_see_and_check():
    body = commands.pr_body(summary="s", changes=[("a", "b")], evidence="e",
                            findings=[("S1", "none", "-", "-")], refs=["#1"])

    assert "See" not in body
    assert "Check before merging" not in body
    assert body.endswith("## Refs\nRefs #1\n")


@pytest.mark.unit
def test_pr_body_without_refs_gives_the_no_ticket_reason():
    body = commands.pr_body(summary="s", changes=[("a", "b")], evidence="e",
                            findings=[("S1", "none", "-", "-")], no_ticket="a typo fix")

    assert body.endswith("## Refs\nNo ticket: a typo fix\n")


@pytest.mark.unit
def test_pr_body_needs_refs_or_a_no_ticket_reason():
    with pytest.raises(commands.GiteaError):
        commands.pr_body(summary="s", changes=[("a", "b")], evidence="e", findings=[])


@pytest.mark.unit
def test_milestone_pointers_post_a_done_pointer_per_closed_ticket(gitea):
    gitea.add_issue(1, title="Home menu", state="closed", milestone="v0.8.0 – Guide")
    gitea.add_issue(2, title="Other release", state="closed", milestone="v0.9.0 – Next")
    gitea.add_issue(3, title="Still open", milestone="v0.8.0 – Guide")
    gitea.add_issue(4, title="Token report", state="closed", milestone="v0.8.0 – Guide")

    posted = commands.milestone_pointers(gitea.call, REPO, "v0.8.0 – Guide", "2026-10-29")

    assert [p["number"] for p in posted] == [1, 4]
    assert gitea.comments[1][-1]["body"] == "Released v0.8.0 – Guide, 2026-10-29. Done: Home menu. → #1"
    assert gitea.comments[2] == [] and gitea.comments[3] == []


TEMPLATE = ("# Definition of Done - Review Worksheet\n\n"
            "**Project:** **\_\_\_** **Date:** **\_\_\_** **Engineer:** **\_\_\_**\n\n---\n\n"
            "## Stage 1\n\n| Criteria | Eng |\n|---|---|\n| README | ☐ |\n\n---\n\n"
            "## Sign-Off\n\n| Stage | Engineer |\n|---|---|\n| Approved | ☐ |\n")


@pytest.mark.unit
def test_worksheet_prefills_evidence_and_leaves_judgement_and_sign_off():
    sheet = commands.worksheet(
        TEMPLATE, project="Repo", date="2026-10-29",
        tickets=[(121, "Fixed texts")], pulls=[(210, "DoD column")], tests="159 passed",
        findings=[("S1", "Name is vague", "low", "Fixed (abc1234)")])

    assert sheet.startswith("# Definition of Done - Review Worksheet\n\n**Project:** Repo **Date:** 2026-10-29 ")
    assert "- #121 Fixed texts" in sheet and "- #210 DoD column" in sheet
    assert "Tests: 159 passed" in sheet
    assert "| S1 | Name is vague | low | Fixed (abc1234) |" in sheet
    assert "| README | ☐ |" in sheet and "| Approved | ☐ |" in sheet
    assert sheet.index("Evidence") < sheet.index("## Stage 1")


@pytest.mark.unit
def test_saving_counts_the_filled_text_the_model_no_longer_writes():
    from dp import tokens
    assert tokens.saving("abcdefgh" * 10, "abcdefgh") == 18
