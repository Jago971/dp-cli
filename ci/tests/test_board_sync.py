"""Tests for ci/board_sync.py at its move() seam, against an in-memory Gitea."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import board_sync  # noqa: E402
from fake_gitea import FakeGitea  # noqa: E402


@pytest.fixture
def gitea(monkeypatch):
    fake = FakeGitea()
    monkeypatch.setattr(board_sync, "call", fake.call)
    return fake


def test_a_ticket_past_the_first_page_of_a_column_is_moved_not_re_added(gitea):
    gitea.put("Backlog", *range(1, 56))  # 55 tickets; #55 is on page 2

    board_sync.move("Org/Repo", 55, "In Progress", forward_only=False)

    assert gitea.column_of(55) == "In Progress"
    assert gitea.writes == [("move", 55)]


def test_a_ticket_not_on_the_board_is_placed_in_the_column(gitea):
    gitea.put("Backlog", *range(1, 51))  # a full first page, and no #99

    board_sync.move("Org/Repo", 99, "Triage", forward_only=False)

    assert gitea.column_of(99) == "Triage"
    assert gitea.writes == [("add", 99)]


def test_a_ticket_further_along_on_a_later_page_is_not_moved_back(gitea):
    gitea.put("DoD", *range(1, 56))

    board_sync.move("Org/Repo", 55, "Testing", forward_only=True)

    assert gitea.column_of(55) == "DoD"
    assert gitea.writes == []
