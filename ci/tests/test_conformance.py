"""Tests for ci/conformance.py at its check seams."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import conformance  # noqa: E402


def pull_request_with(monkeypatch, tmp_path, body):
    path = tmp_path / "event.json"
    path.write_text(json.dumps({"pull_request": {"number": 9, "body": body}}), encoding="utf-8")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(path))


@pytest.mark.unit
def test_pr_ticket_only_other_repo_ticket_fails(monkeypatch, tmp_path):
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
