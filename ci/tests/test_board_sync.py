"""Tests for ci/board_sync.py at its main(), tickets_named() and move() seams; main() and move() run against an in-memory Gitea."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import board_sync  # noqa: E402
from fake_gitea import FakeGitea  # noqa: E402


def use(monkeypatch, fake):
    monkeypatch.setattr(board_sync, "call", fake.call)
    return fake


@pytest.fixture
def gitea(monkeypatch):
    return use(monkeypatch, FakeGitea())


def run_event(monkeypatch, tmp_path, event):
    path = tmp_path / "event.json"
    path.write_text(json.dumps(event), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(path))
    monkeypatch.setenv("REPOSITORY", "Org/Repo")
    board_sync.main()


@pytest.mark.unit
def test_move_ticket_on_second_page_moves_it_not_adds(gitea):
    gitea.put("Backlog", *range(1, 56))  # 55 tickets; #55 is on page 2

    board_sync.move("Org/Repo", 55, "In Progress", forward_only=False)

    assert gitea.column_of(55) == "In Progress"
    assert gitea.writes == [("move", 55)]


@pytest.mark.unit
def test_move_ticket_not_on_board_adds_it(gitea):
    gitea.put("Backlog", *range(1, 51))  # a full first page, and no #99

    board_sync.move("Org/Repo", 99, "Triage", forward_only=False)

    assert gitea.column_of(99) == "Triage"
    assert gitea.writes == [("add", 99)]


@pytest.mark.unit
def test_move_backward_ticket_on_later_page_leaves_it(gitea):
    gitea.put("DoD", *range(1, 56))

    board_sync.move("Org/Repo", 55, "Testing", forward_only=True)

    assert gitea.column_of(55) == "DoD"
    assert gitea.writes == []


@pytest.mark.unit
def test_move_with_smaller_server_page_size_still_finds_ticket(monkeypatch):
    gitea = use(monkeypatch, FakeGitea(page_size=30))  # MAX_RESPONSE_ITEMS set lower
    gitea.put("Backlog", *range(1, 41))

    board_sync.move("Org/Repo", 35, "In Progress", forward_only=False)

    assert gitea.column_of(35) == "In Progress"
    assert gitea.writes == [("move", 35)]


@pytest.mark.unit
def test_move_when_server_ignores_page_fails_instead_of_looping(monkeypatch):
    gitea = use(monkeypatch, FakeGitea(ignores_page=True))
    gitea.put("Backlog", *range(1, 56))

    with pytest.raises(RuntimeError, match="pages"):
        board_sync.move("Org/Repo", 55, "In Progress", forward_only=False)
    assert gitea.writes == []


@pytest.mark.unit
def test_tickets_named_takes_refs_and_branch_not_see():
    pull = {"number": 9, "head": {"ref": "fix/3-slug"},
            "body": "## Refs\nRefs #1 · Other/Repo#4\nSee #2\n"}

    assert board_sync.tickets_named(pull) == [1, 3]


@pytest.mark.unit
def test_tickets_moved_takes_the_branch_not_refs_or_see():
    pull = {"number": 9, "head": {"ref": "fix/3-slug"},
            "body": "## Refs\nRefs #1 and Other/Repo#4\nSee #2\n"}

    assert board_sync.tickets_moved(pull) == [3]


@pytest.mark.unit
def test_issue_opened_off_the_board_lands_in_triage(gitea, monkeypatch, tmp_path):
    run_event(monkeypatch, tmp_path, {"action": "opened", "issue": {"number": 7}})

    assert gitea.column_of(7) == "Triage"
    assert gitea.writes == [("add", 7)]


@pytest.mark.unit
def test_issue_opened_already_on_the_board_keeps_its_column(gitea, monkeypatch, tmp_path):
    gitea.put("Backlog", 7)

    run_event(monkeypatch, tmp_path, {"action": "opened", "issue": {"number": 7}})

    assert gitea.column_of(7) == "Backlog"
    assert gitea.writes == []


@pytest.mark.unit
def test_issue_closed_waits_in_dod_for_the_gate(gitea, monkeypatch, tmp_path):
    gitea.put("Testing", 7)

    run_event(monkeypatch, tmp_path, {"action": "closed", "issue": {"number": 7}})

    assert gitea.column_of(7) == "DoD"


@pytest.mark.unit
def test_issue_closed_already_in_dod_keeps_its_column(gitea, monkeypatch, tmp_path):
    gitea.put("DoD", 7)

    run_event(monkeypatch, tmp_path, {"action": "closed", "issue": {"number": 7}})

    assert gitea.column_of(7) == "DoD"
    assert gitea.writes == []


def release_event(milestone="v1.0", base="main", head="prep", merged=True):
    return {"action": "closed", "pull_request": {
        "number": 90, "merged": merged, "base": {"ref": base}, "head": {"ref": head},
        "milestone": {"title": milestone} if milestone else None}}


@pytest.mark.unit
def test_release_merge_moves_milestone_dod_tickets_to_done_and_comments(gitea, monkeypatch, tmp_path, capsys):
    gitea.add_issue(1, milestone="v1.0", state="closed")
    gitea.add_issue(2, milestone="v1.0")
    gitea.add_issue(3, milestone="v2.0", state="closed")
    gitea.put("DoD", 1, 3)
    gitea.put("Testing", 2)

    run_event(monkeypatch, tmp_path, release_event())

    assert gitea.column_of(1) == "Done"
    assert gitea.column_of(2) == "Testing"
    assert gitea.column_of(3) == "DoD"
    assert [w for w in gitea.writes if w[0] == "comment"] == [("comment", 1, "Released in v1.0 (#90).")]
    assert "LEAVE #2: in Testing, not DoD" in capsys.readouterr().out


@pytest.mark.unit
@pytest.mark.parametrize("event", [
    release_event(base="prep", head="feat/1-x"),
    release_event(merged=False),
    release_event(milestone=None)])
def test_release_move_needs_a_merged_prep_to_main_pull_with_a_milestone(gitea, monkeypatch, tmp_path, event):
    gitea.add_issue(1, milestone="v1.0", state="closed")
    gitea.put("DoD", 1)

    run_event(monkeypatch, tmp_path, event)

    assert gitea.column_of(1) == "DoD"
    assert gitea.writes == []
