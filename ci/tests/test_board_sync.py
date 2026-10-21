"""Tests for ci/board_sync.py at its tickets_named() and move() seams, move() against an in-memory Gitea."""
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
