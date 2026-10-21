"""Tests for ci/conformance.py at its check seams."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import conformance  # noqa: E402


def pull_request_with(monkeypatch, tmp_path, body):
    path = tmp_path / "event.json"
    pull = {"number": 9, "head": {"ref": "chore/tidy"}, "body": body}
    path.write_text(json.dumps({"pull_request": pull}), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(path))


@pytest.mark.unit
def test_pr_ticket_names_only_other_repo_ticket_fails(monkeypatch, tmp_path):
    pull_request_with(monkeypatch, tmp_path, "## Refs\nSee Datumpin/DEVKIT#44\n")

    ok, _ = conformance.check_pr_ticket(tmp_path)

    assert not ok


@pytest.mark.unit
def test_pr_ticket_no_ticket_line_passes(monkeypatch, tmp_path):
    pull_request_with(monkeypatch, tmp_path, "## Refs\nNo ticket: one-line docs fix\n")

    ok, _ = conformance.check_pr_ticket(tmp_path)

    assert ok


@pytest.mark.unit
def test_pr_ticket_local_ticket_passes(monkeypatch, tmp_path):
    pull_request_with(monkeypatch, tmp_path, "## Refs\nRefs #12\n")

    ok, _ = conformance.check_pr_ticket(tmp_path)

    assert ok


@pytest.mark.unit
def test_pr_ticket_names_local_ticket_only_under_see_fails(monkeypatch, tmp_path):
    pull_request_with(monkeypatch, tmp_path, "## Refs\nRefs #9\nSee #5\n")  # #9 is the PR itself

    ok, _ = conformance.check_pr_ticket(tmp_path)

    assert not ok


@pytest.mark.unit
def test_pr_ticket_without_pull_request_event_passes(monkeypatch, tmp_path):
    monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)

    ok, _ = conformance.check_pr_ticket(tmp_path)

    assert ok
