"""Unit tier: dp's command line (plugins/datumpin/dp), with Gitea in memory."""
import json

import pytest
from typer.testing import CliRunner

from dp import cli
from dp.gitea import GiteaError
from fake_gitea import FakeGitea


@pytest.fixture
def gitea(monkeypatch):
    fake = FakeGitea()
    connection = cli.Connection(call=fake.call, repo="Org/Repo", human=lambda: "MattM")
    monkeypatch.setattr(cli, "connect", lambda: connection)
    return fake


def run(*args, **env):
    return CliRunner().invoke(cli.app, list(args), env=env)


@pytest.mark.unit
def test_json_prints_the_command_result(gitea):
    gitea.add_issue(4)
    gitea.put("Backlog", 4)

    result = run("move", "4", "In Progress", "--json")

    assert result.exit_code == 0
    assert json.loads(result.output) == {"number": 4, "from": "Backlog", "to": "In Progress",
                                         "assigned": "MattM"}


@pytest.mark.unit
def test_move_with_an_assignee_skips_looking_up_the_human(gitea, monkeypatch):
    def several_humans():
        raise GiteaError("need exactly one human tea login besides squire; found: matt, ops")

    monkeypatch.setattr(cli.connect(), "human", several_humans)
    gitea.add_issue(4)
    gitea.put("Backlog", 4)

    result = run("move", "4", "In Progress", "--assignee", "Ops", "--json")

    assert result.exit_code == 0
    assert json.loads(result.output)["assigned"] == "Ops"


@pytest.mark.unit
def test_board_honours_no_color_even_when_colour_is_forced(gitea):
    gitea.add_issue(4, title="Ticket", labels=["TYPE/BUG"])
    gitea.put("Backlog", 4)

    result = run("board", FORCE_COLOR="1", NO_COLOR="1")

    assert result.exit_code == 0
    assert "#4 Ticket" in result.output
    assert "\x1b[" not in result.output


@pytest.mark.unit
def test_pr_reads_its_body_from_a_file(gitea, tmp_path, monkeypatch):
    body = tmp_path / "pr.md"
    body.write_text("## Summary\nWhy.\n", encoding="utf-8")
    monkeypatch.setattr(cli, "current_branch", lambda: "feat/4-x")

    result = run("pr", "--title", "Title", "--body-file", str(body), "--json")

    assert result.exit_code == 0
    assert gitea.writes[0][1]["body"] == "## Summary\nWhy.\n"
    assert gitea.writes[0][1]["head"] == "feat/4-x"


@pytest.mark.unit
def test_a_gitea_error_prints_one_line_and_exits_1(monkeypatch):
    def unreachable():
        raise GiteaError("Gitea unreachable: connection refused")

    monkeypatch.setattr(cli, "connect", unreachable)

    result = run("board")

    assert result.exit_code == 1
    assert result.output.strip() == "dp: Gitea unreachable: connection refused"
