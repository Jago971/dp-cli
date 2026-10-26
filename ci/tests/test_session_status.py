"""Unit tier: the session-start status hook reads the repo's agent login safely."""
import importlib.util
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[2] / "plugins" / "datumpin" / "hooks" / "session_status.py"
spec = importlib.util.spec_from_file_location("session_status", HOOK)
session_status = importlib.util.module_from_spec(spec)
spec.loader.exec_module(session_status)


def flow(tmp_path, value):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "flow.yaml").write_text(f"gitea:\n  agent_login: {value}\n", encoding="utf-8")


@pytest.mark.unit
def test_agent_login_reads_the_repo_flow_config(tmp_path):
    flow(tmp_path, "bot")

    assert session_status.agent_login(str(tmp_path)) == "bot"


@pytest.mark.unit
@pytest.mark.parametrize("value", ["--insecure", "-x", "a;b", "bad'name"])
def test_agent_login_falls_back_to_the_default_on_a_bad_value(tmp_path, value):
    flow(tmp_path, value)

    assert session_status.agent_login(str(tmp_path)) == "squire"
