"""Tests for plugins/datumpin/bin/token_report.py at its report() seam."""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "plugins", "datumpin", "bin"))
import token_report  # noqa: E402


def turn(cache_read, tool=None):
    """One assistant turn of a session log, as a JSON line."""
    content = [tool] if tool else [{"type": "text", "text": "..."}]
    usage = {"input_tokens": 1, "output_tokens": 2, "cache_read_input_tokens": cache_read,
             "cache_creation_input_tokens": 0}
    return json.dumps({"type": "assistant", "message": {"content": content, "usage": usage}})


def state_write(step):
    return {"type": "tool_use", "name": "Bash",
            "input": {"command": f"printf 'flow: ticket\\nstep: {step}\\n' > .factory/guide.yaml"}}


def skill(name):
    return {"type": "tool_use", "name": "Skill", "input": {"skill": name}}


def by_step(rows):
    return {row["step"]: row for row in rows}


@pytest.mark.unit
def test_report_books_each_turn_to_the_step_its_next_state_write_names():
    log = [turn(10), turn(5, state_write("pick")), turn(7), turn(1, state_write("build"))]

    rows = by_step(token_report.report(log))

    assert (rows["pick"]["turns"], rows["pick"]["cache_read"]) == (2, 15)
    assert (rows["build"]["turns"], rows["build"]["cache_read"]) == (2, 8)


@pytest.mark.unit
def test_report_without_state_writes_splits_on_skill_calls():
    log = [turn(3, skill("datumpin:tdd")), turn(4), turn(2, skill("datumpin:change-review"))]

    rows = by_step(token_report.report(log))

    assert (rows["datumpin:tdd"]["turns"], rows["datumpin:tdd"]["cache_read"]) == (2, 7)
    assert (rows["datumpin:change-review"]["turns"], rows["datumpin:change-review"]["tools"]) == (1, 1)
