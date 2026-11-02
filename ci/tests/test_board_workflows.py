"""Tests for how board.yml and board-sync.yml choose the board_sync.py they run.

Unit tier: parses the workflow files, runs nothing.
"""
import os

import pytest
import yaml

WORKFLOWS = os.path.join(os.path.dirname(__file__), "..", "..", ".gitea", "workflows")

pytestmark = pytest.mark.unit


def load(name):
    with open(os.path.join(WORKFLOWS, name), encoding="utf-8") as f:
        return yaml.safe_load(f)


def trigger(workflow):
    # YAML 1.1 reads the bare key `on` as True.
    return workflow.get("on", workflow.get(True))


def test_other_repos_get_main_by_default():
    ref = trigger(load("board-sync.yml"))["workflow_call"]["inputs"]["ref"]
    assert ref["default"] == "main"


def test_board_sync_checks_out_the_ref_input():
    steps = load("board-sync.yml")["jobs"]["board"]["steps"]
    fetch = next(s for s in steps if s.get("with", {}).get("repository") == "Datumpin/DEVKIT")
    assert fetch["with"]["ref"] == "${{ inputs.ref }}"


def test_devkit_board_run_passes_its_own_sha():
    job = load("board.yml")["jobs"]["board"]
    assert job["with"]["ref"] == "${{ github.sha }}"
