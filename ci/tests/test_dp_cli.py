"""Unit tier: dp's command line (plugins/datumpin/dp), with Gitea in memory."""
import json
import tomllib
from pathlib import Path

import pytest
from typer.testing import CliRunner

from dp import cli
from dp.gitea import GiteaError
from fake_gitea import FakeGitea

PYPROJECT = Path(__file__).parents[2] / "plugins/datumpin/dp/pyproject.toml"


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
    assert result.output.strip() == "✖ dp: Gitea unreachable: connection refused"


@pytest.mark.unit
def test_guide_json_prints_the_position_and_the_choices(gitea, tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "repo_root", lambda: tmp_path)
    (tmp_path / ".factory").mkdir()
    (tmp_path / ".factory" / "guide.yaml").write_text("flow: ticket\nstep: review\nticket: 4\n")
    gitea.add_issue(4)
    gitea.put("In Progress", 4)

    result = run("guide", "--json")

    assert result.exit_code == 0
    shown = json.loads(result.output)
    assert shown["position"] == {"flow": "ticket", "step": "review", "ticket": 4}
    assert shown["env"] == "dev"
    assert [choice["step"] for choice in shown["choices"]] == ["fix", "pr"]


@pytest.mark.unit
def test_guide_off_a_terminal_prints_the_guide_prompt(gitea, tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "repo_root", lambda: tmp_path)

    result = run("guide")

    assert result.exit_code == 0
    assert result.output.splitlines()[0] == "Guide · start"
    assert "1. tickets" in result.output
    assert result.output.rstrip().endswith("? Next? (1 / 2 / 3 / 4)")


@pytest.mark.unit
def test_pick_takes_a_ticket_in_on_its_branch(gitea, monkeypatch):
    branched = []
    monkeypatch.setattr(cli, "git", lambda *args: branched.append(args) or "")
    gitea.add_issue(4, title="Fix the thing", labels=["TYPE/BUG"], milestone="v1")
    gitea.put("Backlog", 4)

    result = run("pick", "4", "--json")

    assert result.exit_code == 0
    taken = json.loads(result.output)
    assert (taken["to"], taken["assigned"], taken["branch"]) == ("In Progress", "MattM", "fix/4-fix-the-thing")
    assert branched == [("switch", "--create=fix/4-fix-the-thing", "prep")]


@pytest.mark.unit
def test_pick_passes_a_leading_dash_branch_as_a_value_not_an_option(gitea, monkeypatch):
    branched = []
    monkeypatch.setattr(cli, "git", lambda *args: branched.append(args) or "")
    gitea.add_issue(4, title="Fix the thing", labels=["TYPE/BUG"], milestone="v1")
    gitea.put("Backlog", 4)

    result = run("pick", "4", "--branch=-x", "--json")

    assert result.exit_code == 0
    assert branched == [("switch", "--create=-x", "prep")]


@pytest.mark.unit
def test_pick_without_a_number_off_a_terminal_asks_for_one(gitea):
    result = run("pick")

    assert result.exit_code == 1
    assert "dp pick N" in result.output


@pytest.mark.unit
def test_plain_drops_colour_even_when_colour_is_forced(gitea):
    gitea.add_issue(4, title="Ticket", labels=["STATUS/BLOCKED"])
    gitea.put("In Progress", 4)

    result = run("--plain", "board", FORCE_COLOR="1")

    assert result.exit_code == 0
    assert "#4 Ticket · STATUS/BLOCKED" in result.output
    assert "\x1b[" not in result.output


@pytest.mark.unit
def test_a_write_ends_with_one_tick_line(gitea):
    gitea.add_issue(4)
    gitea.put("Backlog", 4)

    result = run("move", "4", "Review")

    assert result.output.strip() == "✔ #4 Backlog → Review"


@pytest.fixture
def installed_version(monkeypatch):
    """Stand in for the installed dp, and fail when dp asks for any other distribution name."""
    name = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]["name"]
    version = "1.2.3"
    monkeypatch.setattr("importlib.metadata.version", lambda asked: version if asked == name else "?")
    return version


@pytest.mark.unit
def test_version_command_prints_the_installed_version(installed_version):
    result = run("version")

    assert result.exit_code == 0
    assert result.output.strip() == f"dp {installed_version}"


@pytest.mark.unit
def test_version_flag_prints_the_same_as_the_command(installed_version):
    result = run("--version")

    assert result.exit_code == 0
    assert result.output.strip() == f"dp {installed_version}"


@pytest.mark.unit
def test_pointers_posts_a_done_pointer_per_closed_ticket(gitea):
    gitea.add_issue(1, title="Home menu", state="closed", milestone="v0.8.0")

    result = run("pointers", "v0.8.0", "--json")

    assert result.exit_code == 0
    shown = json.loads(result.output)
    assert [p["number"] for p in shown["pointers"]] == [1]
    assert shown["saved_tokens"] > 0


@pytest.mark.unit
def test_pr_body_with_bad_json_fails_on_one_line(tmp_path):
    parts = tmp_path / "parts.json"
    parts.write_text("{not json")

    result = run("pr-body", str(parts))

    assert result.exit_code == 1
    assert "Traceback" not in result.output
    assert "dp:" in result.output


@pytest.mark.unit
def test_pr_body_prints_the_body_and_the_saving(tmp_path):
    parts = tmp_path / "parts.json"
    parts.write_text(json.dumps({"summary": "s", "changes": [["a", "b"]], "evidence": "e",
                                 "findings": [["S1", "none", "-", "-"]], "refs": ["#1"]}))

    result = run("pr-body", str(parts), "--json")

    out = json.loads(result.output)
    assert out["body"].startswith("## Summary\ns\n") and out["saved_tokens"] >= 0


@pytest.mark.unit
def test_worksheet_prints_the_filled_sheet(tmp_path):
    parts = tmp_path / "parts.json"
    parts.write_text(json.dumps({"project": "Repo", "tickets": [[1, "T"]], "pulls": [[2, "P"]],
                                 "tests": "5 passed", "findings": [["S1", "none", "-", "-"]]}))
    template = tmp_path / "t.md"
    template.write_text("# W\n\n**Project:** **\_\_\_** **Date:** **\_\_\_**\n\n---\n\n## Sign-Off\n")

    result = run("worksheet", str(parts), "--template", str(template), "--json")

    assert "**Project:** Repo" in json.loads(result.output)["worksheet"]
