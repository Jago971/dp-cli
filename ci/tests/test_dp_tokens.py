"""Unit tier: dp tokens (plugins/datumpin/dp) at its report() seam."""
import json

import pytest

from dp import tokens


def turn(cache_read, tool=None, message_id=None):
    """One assistant turn of a session log, as a JSON line."""
    content = [tool] if tool else [{"type": "text", "text": "..."}]
    usage = {"input_tokens": 1, "output_tokens": 2, "cache_read_input_tokens": cache_read,
             "cache_creation_input_tokens": 0}
    message = {"content": content, "usage": usage, **({"id": message_id} if message_id else {})}
    return json.dumps({"type": "assistant", "message": message})


def state_write(step):
    return {"type": "tool_use", "name": "Bash",
            "input": {"command": f"printf 'flow: ticket\\nstep: {step}\\n' > .factory/guide.yaml"}}


def skill(name):
    return {"type": "tool_use", "name": "Skill", "input": {"skill": name}}


def edit(file_path, old, new):
    return {"type": "tool_use", "name": "Edit",
            "input": {"file_path": file_path, "old_string": old, "new_string": new}}


def by_step(rows):
    return {row["step"]: row for row in rows}


@pytest.mark.unit
def test_report_books_each_turn_to_the_step_its_next_state_write_names():
    log = [turn(10), turn(5, state_write("pick")), turn(7), turn(1, state_write("build"))]

    rows = by_step(tokens.report(log))

    assert (rows["pick"]["turns"], rows["pick"]["cache_read"]) == (2, 15)
    assert (rows["build"]["turns"], rows["build"]["cache_read"]) == (2, 8)


@pytest.mark.unit
def test_report_without_state_writes_splits_on_skill_calls():
    log = [turn(3, skill("datumpin:tdd")), turn(4), turn(2, skill("datumpin:change-review"))]

    rows = by_step(tokens.report(log))

    assert (rows["datumpin:tdd"]["turns"], rows["datumpin:tdd"]["cache_read"]) == (2, 7)
    assert (rows["datumpin:change-review"]["turns"], rows["datumpin:change-review"]["tools"]) == (1, 1)


@pytest.mark.unit
def test_report_counts_the_lines_of_one_response_as_one_turn():
    log = [turn(10, skill("datumpin:tdd"), message_id="msg_1"), turn(10, message_id="msg_1")]

    rows = by_step(tokens.report(log))

    assert (rows["datumpin:tdd"]["turns"], rows["datumpin:tdd"]["cache_read"]) == (1, 10)


@pytest.mark.unit
def test_report_reads_the_new_step_from_an_edit_of_the_state_file_only():
    log = [turn(1, edit(r"C:\repo\.factory\guide.yaml", "step: pick", "step: build")),
           turn(2, edit("skills/guide/SKILL.md", "", "Write `step: review` to .factory/guide.yaml."))]

    rows = by_step(tokens.report(log))

    assert list(rows) == ["build"]
    assert rows["build"]["turns"] == 2
