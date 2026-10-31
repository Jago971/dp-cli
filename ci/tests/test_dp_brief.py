"""Unit tier: dp's job briefs (dp.brief), from the skills packaged with dp."""
import json

import pytest

from dp import brief, flows

MARKDOWN = """# Title

## Wanted
Keep this.

```
## Not a heading
```

### Inside
Still wanted.

## Next
Not wanted.
"""


def job(step="build", **given):
    return brief.Job(**{"flow": "ticket", "step": step, "does": "Agree the seams, then build",
                        "env": "dev", "ticket": {"number": 4, "title": "A ticket", "body": "The body.",
                                                 "comments": [{"author": "MattM", "text": "Go."}]},
                        "column": "In Progress", "diffstat": " a.py | 2 +-", "skills": "SKILL TEXT",
                        **given})


@pytest.mark.unit
def test_a_section_runs_to_the_next_heading_of_its_level_outside_code():
    found = brief.section(MARKDOWN, "Wanted")

    assert found.startswith("## Wanted")
    assert "## Not a heading" in found and "Still wanted." in found
    assert "Not wanted." not in found


@pytest.mark.unit
def test_a_step_without_a_brief_list_carries_its_whole_skill():
    text = brief.skill_text({"skill": "tdd"})

    assert text.startswith("# Test-Driven Development")
    assert "name: tdd" not in text


@pytest.mark.unit
def test_a_brief_list_carries_only_its_sections():
    text = brief.skill_text({"skill": "agent", "brief": ["formats#Commit"]})

    assert text.startswith("## Commit")
    assert "## Branch" not in text


@pytest.mark.unit
def test_agent_and_human_steps_without_a_brief_list_carry_no_skill():
    assert brief.skill_text({"skill": "agent"}) == ""
    assert brief.skill_text({"skill": "human"}) == ""


@pytest.mark.unit
def test_user_invoked_skills_are_typed_not_briefed():
    assert brief.user_invoked("handoff")
    assert not brief.user_invoked("tdd")
    assert not brief.user_invoked("human")


@pytest.mark.unit
def test_a_brief_holds_the_ticket_its_comments_column_diff_and_skill(tmp_path):
    path = brief.write(tmp_path, job())
    text = path.read_text(encoding="utf-8")

    assert path == tmp_path / ".factory" / "jobs" / "4" / "build.md"
    for part in ("#4 A ticket", "The body.", "MattM", "Go.", "In Progress", "a.py | 2 +-", "SKILL TEXT"):
        assert part in text
    assert brief.prompt(job(), path.relative_to(tmp_path)) == \
        "Step build of #4: read .factory/jobs/4/build.md and do it."


@pytest.mark.unit
def test_a_step_without_a_ticket_files_its_brief_under_the_flow(tmp_path):
    release = job("gate", flow="release", ticket=None, column=None)

    path = brief.write(tmp_path, release)

    assert path == tmp_path / ".factory" / "jobs" / "release" / "gate.md"
    assert brief.prompt(release, path.relative_to(tmp_path)) == \
        "Step gate of the release flow: read .factory/jobs/release/gate.md and do it."


@pytest.mark.unit
def test_a_review_brief_asks_for_the_findings_file(tmp_path):
    text = brief.write(tmp_path, job("review")).read_text(encoding="utf-8")

    assert ".factory/jobs/4/findings.json" in text


@pytest.mark.unit
def test_a_fix_brief_lists_the_findings_with_their_dispositions(tmp_path):
    findings = [{"id": "S1", "file": "a.py", "line": 3, "severity": "low", "finding": "Too long",
                 "disposition": "Fix"}]
    folder = tmp_path / ".factory" / "jobs" / "4"
    folder.mkdir(parents=True)
    (folder / "findings.json").write_text(json.dumps(findings), encoding="utf-8")

    text = brief.write(tmp_path, job("fix")).read_text(encoding="utf-8")

    assert "| S1 | a.py:3 Too long | low | Fix |" in text


@pytest.mark.unit
def test_every_brief_section_the_map_names_is_in_its_skill():
    for name, step in flows.load()["steps"].items():
        if "brief" in step:
            assert brief.skill_text(step), name


@pytest.mark.unit
def test_a_brief_section_is_found_in_a_skills_sibling_file():
    text = brief.skill_text({"skill": "agent", "brief": ["docker-compose-conventions#Cron services"]})

    assert text.startswith("# Cron services")


@pytest.mark.unit
def test_every_brief_carries_the_step_ending_rule(tmp_path):
    text = brief.write(tmp_path, job()).read_text(encoding="utf-8")
    assert "Step ending" in text
    assert "numbered choices" in text and "the recommended one first" in text
    assert "`Other` last" in text
    assert "stay or `/exit`, and what `dp guide` then offers" in text


@pytest.mark.unit
def test_formats_defines_the_step_ending_block_beside_the_handover_block():
    text = brief.data("skills", "formats", "terminal.md").read_text(encoding="utf-8")
    assert text.index("## Handover") < text.index("## Step ending") < text.index("## Guide prompt")


@pytest.mark.unit
def test_the_check_brief_names_the_dev_container_test_command():
    text = brief.skill_text(flows.load()["steps"]["check"])
    assert "ci/local-check.sh" in text
    assert "docker compose <dev> exec <service> python -m pytest" in text


def handover_block():
    text = brief.data("skills", "formats", "terminal.md").read_text(encoding="utf-8")
    return text.split("## Handover")[1].split("## Step ending")[0]


@pytest.mark.unit
def test_the_handover_block_is_fenced_with_a_repo_relative_forward_slash_path():
    block = handover_block()
    assert block.count("```") == 2
    assert ".factory/handoff-" in block
    assert "\\" not in block


@pytest.mark.unit
def test_the_handover_next_prompt_tells_the_user_to_run_dp_guide_not_start_a_ticket():
    line = next(l for l in handover_block().splitlines() if l.startswith("Next prompt"))
    assert "dp guide" in line
    assert "continue #" not in line and "/datumpin:board" not in line
    assert "paste" not in line
    assert "does not start the ticket" in line


@pytest.mark.unit
def test_the_handoff_skill_never_tells_the_next_chat_to_start_a_ticket():
    text = brief.data("skills", "handoff", "SKILL.md").read_text(encoding="utf-8")
    assert "never tells the chat to start or build a ticket" in text
    assert "run `dp guide` in dp-cli" in text
    assert "repo-relative" in text
