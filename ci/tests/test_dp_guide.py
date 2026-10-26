"""Unit tier: dp guide's walk (dp.guide), with Gitea in memory and the prompts scripted."""
import json
from types import SimpleNamespace

import pytest

from dp import guide
from dp.gitea import GiteaError
from fake_gitea import FakeGitea


class Script(guide.Plain):
    """The person at the terminal: answers in order, and what the guide said."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.said = []
        self.menus = []  # each menu's labels, and the value it preselected

    def choose(self, message, options, default=None):
        self.menus.append(([label for label, _ in options], default))
        wanted = self.answers.pop(0)
        return next(value for label, value in options if label.split()[0] == wanted)

    def confirm(self, message):
        return self.answers.pop(0)

    def text(self, message, default):
        given = self.answers.pop(0)
        return default if given is None else given

    def say(self, line):
        self.said.append(line)


class Git:
    def __init__(self):
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        return " a.py | 2 +-" if args[0] == "diff" else ""


@pytest.fixture
def gitea():
    fake = FakeGitea()
    fake.connection = SimpleNamespace(call=fake.call, repo="Org/Repo", human=lambda: "MattM")
    return fake


def walk(root, script, gitea, git=None):
    connection = gitea.connection if gitea else guide.offline(GiteaError("Gitea unreachable"))
    guide.walk(root, script, connection, git or Git())


def saved(root):
    return guide.read_state(root)


@pytest.mark.unit
def test_pick_moves_the_ticket_and_branches_from_prep(tmp_path, gitea):
    gitea.add_issue(4, title="Fix the thing: in detail", labels=["TYPE/BUG"], milestone="v1.0.0")
    gitea.put("Backlog", 4)
    git = Git()

    walk(tmp_path, Script("ticket", "#4", None, "stop"), gitea, git)

    assert gitea.column_of(4) == "In Progress"
    assert not [w for w in gitea.writes if w[0] == "milestone"]
    assert git.calls == [("switch", "-c", "fix/4-fix-the-thing", "prep")]
    assert (saved(tmp_path)["step"], saved(tmp_path)["ticket"]) == ("pick", 4)


@pytest.mark.unit
def test_an_agent_step_writes_its_brief_and_prints_the_prompt(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "pick", "ticket": 4})
    gitea.add_issue(4, title="A ticket", comments=[("MattM", "Go.")])
    gitea.put("In Progress", 4)
    script = Script("check", "stop")

    walk(tmp_path, script, gitea)

    assert (tmp_path / ".factory" / "jobs" / "4" / "check.md").is_file()
    assert "Step check of #4: read .factory/jobs/4/check.md and do it." in script.said
    assert saved(tmp_path)["step"] == "check"


@pytest.mark.unit
def test_the_board_corrects_the_state_with_a_log_line(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "pick", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("In Progress", 4)
    script = Script("stop")

    walk(tmp_path, script, gitea)

    assert "[ticket #4] position · pick → build · from the board" in script.said
    assert saved(tmp_path)["step"] == "build"


@pytest.mark.unit
def test_a_human_step_is_recorded_only_once_done(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "pr", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Review", 4)

    walk(tmp_path, Script("merge", False, "stop"), gitea)
    assert saved(tmp_path)["step"] == "pr"

    walk(tmp_path, Script("merge", True, "stop"), gitea)
    assert saved(tmp_path)["step"] == "merge"


@pytest.mark.unit
def test_leaving_review_asks_a_disposition_for_each_finding(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "review", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("In Progress", 4)
    findings = tmp_path / ".factory" / "jobs" / "4" / "findings.json"
    findings.parent.mkdir(parents=True)
    findings.write_text(json.dumps([
        {"id": "S1", "file": "a.py", "line": 3, "severity": "low", "finding": "Too long"},
        {"id": "P1", "file": "b.py", "line": 9, "severity": "medium", "finding": "Not asked for"}]))

    script = Script("Fix", "Dismiss", "out of scope", "fix", "stop")

    walk(tmp_path, script, gitea)

    assert script.menus[2][1]["step"] == "fix"  # the menu after the two findings preselects fix

    decided = [f["disposition"] for f in json.loads(findings.read_text())]
    assert decided == ["Fix", "Dismissed: out of scope"]
    assert "| P1 | b.py:9 Not asked for | medium | Dismissed: out of scope |" in \
        (findings.parent / "fix.md").read_text(encoding="utf-8")


@pytest.mark.unit
def test_a_user_invoked_skill_is_typed_in_the_session(tmp_path):
    guide.write_state(tmp_path, {"flow": "session", "step": "board", "ticket": None})
    script = Script("handoff", "stop")

    walk(tmp_path, script, None)

    assert "Type /datumpin:handoff in the session you worked in." in script.said
    assert not (tmp_path / ".factory" / "jobs").exists()


@pytest.mark.unit
def test_without_gitea_the_state_file_stands(tmp_path):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "review", "ticket": 4})
    script = Script("stop")

    walk(tmp_path, script, None)

    assert "[ticket #4] Gitea unreachable · going on from .factory/guide.yaml" in script.said
    assert saved(tmp_path)["step"] == "review"


@pytest.mark.unit
def test_stop_names_where_to_resume(tmp_path):
    guide.write_state(tmp_path, {"flow": "release", "step": "tag", "ticket": None})
    script = Script("stop")

    walk(tmp_path, script, None)

    assert script.said[-1] == "[release] stopped · resume at tag · dp guide"


@pytest.mark.unit
def test_a_state_with_a_ticket_that_is_not_a_number_drops_it(tmp_path):
    (tmp_path / ".factory").mkdir()
    (tmp_path / ".factory" / "guide.yaml").write_text("flow: ticket\nstep: build\nticket: abc\n")

    assert saved(tmp_path)["ticket"] is None


@pytest.mark.unit
def test_pick_puts_a_ticket_without_a_milestone_in_the_one_due_first(tmp_path, gitea):
    gitea.milestones += [{"id": 1, "title": "v2", "due_on": None},
                         {"id": 2, "title": "v1.1", "due_on": "2026-12-01T00:00:00Z"},
                         {"id": 3, "title": "v1", "due_on": "2026-11-01T00:00:00Z"}]
    gitea.add_issue(4, title="A ticket")
    gitea.put("Backlog", 4)
    script = Script("ticket", "#4", None, "stop")

    walk(tmp_path, script, gitea)

    assert ("milestone", 4, 3) in gitea.writes
    assert "[ticket #4] joined v1" in script.said


@pytest.mark.unit
def test_a_tag_waits_for_the_release_pr_on_main(tmp_path):
    guide.write_state(tmp_path, {"flow": "release", "step": "sign-off", "ticket": None})

    walk(tmp_path, Script("tag", False, "stop"), None)
    assert saved(tmp_path)["step"] == "sign-off"
    assert not (tmp_path / ".factory" / "jobs").exists()

    walk(tmp_path, Script("tag", True, "stop"), None)
    assert (tmp_path / ".factory" / "jobs" / "release" / "tag.md").is_file()


@pytest.mark.unit
def test_findings_left_undecided_are_asked_before_the_next_brief(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "fix", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Review", 4)
    findings = tmp_path / ".factory" / "jobs" / "4" / "findings.json"
    findings.parent.mkdir(parents=True)
    findings.write_text(json.dumps([{"id": "S1", "file": "a.py", "line": 3, "severity": "low",
                                     "finding": "Too long"}]))

    walk(tmp_path, Script("pr", "Escalate", "MattM", "stop"), gitea)

    assert json.loads(findings.read_text())[0]["disposition"] == "Escalated: MattM"


def pointer_tested(number):
    return ("Squire", f"Tested by hand, 2026-10-22. Done: prep. → #{number}")


@pytest.mark.unit
def test_the_menu_puts_this_flow_first_then_the_forks_that_hold(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4, milestone="v1")
    gitea.add_issue(5, milestone="v1")
    gitea.put("Testing", 4, 5)
    script = Script("stop")

    walk(tmp_path, script, gitea)

    labels = [label.split()[0] for label in script.menus[0][0]]
    assert labels == ["pick", "───────────", "board", "flows…", "stop"]  # no gate: #5 is not tested


@pytest.mark.unit
def test_gate_is_offered_once_every_other_ticket_in_the_milestone_is_tested(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4, milestone="v1")
    gitea.add_issue(5, milestone="v1", comments=[pointer_tested(5)])
    gitea.add_issue(6, milestone="v2")
    gitea.put("Testing", 4, 5)
    gitea.put("Backlog", 6)
    script = Script("stop")

    walk(tmp_path, script, gitea)

    assert "gate" in [label.split()[0] for label in script.menus[0][0]]


@pytest.mark.unit
def test_leaving_test_posts_a_pointer_tested(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Testing", 4)

    walk(tmp_path, Script("pick", True, "laptop, names end -dev", "stop"), gitea)

    posted = [w for w in gitea.writes if w[0] == "comment"]
    assert len(posted) == 1
    assert posted[0][2].startswith("Tested by hand, ")
    assert posted[0][2].endswith(". Done: laptop, names end -dev. → #4")


@pytest.mark.unit
def test_an_untested_change_stays_at_test(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Testing", 4)
    script = Script("pick", False, "stop")

    walk(tmp_path, script, gitea)

    assert not [w for w in gitea.writes if w[0] == "comment"]
    assert saved(tmp_path)["step"] == "test"
    assert "[ticket #4] not tested · staying at test" in script.said


@pytest.mark.unit
def test_leaving_the_ticket_flow_pauses_it_and_flows_resumes_it(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4, comments=[pointer_tested(4)])
    gitea.put("Testing", 4)
    script = Script("flows…", "align", True, None, "stop")

    walk(tmp_path, script, gitea)

    assert saved(tmp_path)["flow"] == "align"
    assert saved(tmp_path)["paused"] == {"flow": "ticket", "step": "test", "ticket": 4}

    script = Script("flows…", "resume", "stop")
    walk(tmp_path, script, gitea)

    assert "resume      #4 at test" in script.menus[1][0]
    assert (saved(tmp_path)["flow"], saved(tmp_path)["step"], saved(tmp_path)["ticket"]) == ("ticket", "test", 4)


@pytest.mark.unit
def test_an_agent_step_hands_claude_the_skills_model_and_effort(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "pick", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Backlog", 4)
    handed = []
    script = Script("shape", "stop")
    script.job = lambda prompt, model, effort: handed.append((prompt, model, effort))

    walk(tmp_path, script, gitea)

    assert handed == [("Step shape of #4: read .factory/jobs/4/shape.md and do it.", "opus", "high")]


@pytest.mark.unit
def test_the_end_of_a_flow_lists_the_flows_once(tmp_path):
    guide.write_state(tmp_path, {"flow": "session", "step": "retro", "ticket": None})
    script = Script("stop")

    walk(tmp_path, script, None)

    labels = [label.split()[0] for label in script.menus[0][0]]
    assert labels == ["ticket", "release", "align", "deploy", "session", "stop"]


class Promotion(Git):
    """Git for a release: the stat of the promotion diff, or none."""

    def __init__(self, stat):
        super().__init__()
        self.stat = stat

    def __call__(self, *args):
        self.calls.append(args)
        return self.stat if args[:2] == ("diff", "--stat") and args[-1] == "origin/main...prep" else ""


@pytest.mark.unit
def test_a_release_brief_carries_the_promotion_diff(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "release", "step": "gate", "ticket": None})

    walk(tmp_path, Script("review", "stop"), gitea, Promotion(" b.py | 9 +"))

    text = (tmp_path / ".factory" / "jobs" / "release" / "review.md").read_text(encoding="utf-8")
    assert "b.py | 9 +" in text


@pytest.mark.unit
def test_an_empty_promotion_diff_stops_the_review(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "release", "step": "gate", "ticket": None})
    script = Script("review", "stop")

    walk(tmp_path, script, gitea, Promotion(""))

    assert any("FAILED" in line and "origin/main...prep" in line for line in script.said)
    assert not (tmp_path / ".factory" / "jobs" / "release").exists()
    assert saved(tmp_path)["step"] == "gate"
