"""Unit tier: dp's Gitea seam (plugins/datumpin/dp), with `tea` faked."""
import subprocess

import pytest

from dp import gitea
from dp.gitea import GiteaError


def fake_tea(monkeypatch, status, stdout="", returncode=0, stderr=None):
    """Answer every subprocess.run as `tea api --include` would, and record the calls."""
    seen = []

    def run(args, **kwargs):
        seen.append((args, kwargs.get("input")))
        headers = stderr if stderr is not None else f"HTTP/1.1 {status}\nContent-Type: application/json\n"
        return subprocess.CompletedProcess(args, returncode, stdout, headers)

    monkeypatch.setattr(gitea.subprocess, "run", run)
    return seen


@pytest.mark.unit
def test_call_sends_the_body_on_stdin_and_parses_the_reply(monkeypatch):
    seen = fake_tea(monkeypatch, "201 Created", '{"number": 3}')

    reply = gitea.tea("squire")("POST", "repos/O/R/issues/3/comments", {"body": "line\nline"})

    args, stdin = seen[0]
    assert args[:4] == ["tea", "api", "--include", "--login"] and "squire" in args
    assert ["-X", "POST"] == args[args.index("-X"):args.index("-X") + 2]
    assert stdin == '{"body": "line\\nline"}'
    assert reply == {"number": 3}


@pytest.mark.unit
def test_call_raises_on_an_http_error_although_tea_exits_0(monkeypatch):
    fake_tea(monkeypatch, "404 Not Found", '{"message":"not found"}')

    with pytest.raises(GiteaError, match="404.*not found"):
        gitea.tea("squire")("GET", "repos/O/R/issues/99")


@pytest.mark.unit
def test_call_raises_when_tea_fails(monkeypatch):
    fake_tea(monkeypatch, None, returncode=1, stderr="Error: login name 'x' does not exist\n")

    with pytest.raises(GiteaError, match="login name 'x'"):
        gitea.tea("x")("GET", "user")


@pytest.mark.unit
def test_human_username_is_the_one_login_that_is_not_the_agent():
    logins = [{"name": "matt", "user": "MattM"}, {"name": "squire", "user": "Squire"}]

    assert gitea.human_username(logins, "squire") == "MattM"


@pytest.mark.unit
def test_human_username_with_several_human_logins_asks_for_one():
    logins = [{"name": "matt", "user": "MattM"}, {"name": "ops", "user": "Ops"},
              {"name": "squire", "user": "Squire"}]

    with pytest.raises(GiteaError, match="matt, ops"):
        gitea.human_username(logins, "squire")


@pytest.mark.unit
def test_agent_login_reads_the_repo_flow_config(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "flow.yaml").write_text("gitea:\n  agent_login: bot\n", encoding="utf-8")

    assert gitea.agent_login(tmp_path) == "bot"
    assert gitea.agent_login(tmp_path / "elsewhere") == "squire"


@pytest.mark.unit
def test_repo_slug_is_the_remote_path_without_git():
    assert gitea.repo_slug("ssh://git@host:2222/Datumpin/BDS.git") == "Datumpin/BDS"
    assert gitea.repo_slug("http://host:3393/Datumpin/WIKI") == "Datumpin/WIKI"
