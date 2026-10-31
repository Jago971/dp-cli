"""Unit tier: dp guide's walk (dp.guide), with Gitea in memory and the prompts scripted."""
import json
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from dp import guide
from dp.gitea import GiteaError
from fake_gitea import FakeGitea


HOME = ["tickets", "end", "flows…", "stop"]  # the menu with no ticket current


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

    walk(tmp_path, Script("tickets", "#4", None, "stop"), gitea, git)

    assert gitea.column_of(4) == "In Progress"
    assert not [w for w in gitea.writes if w[0] == "milestone"]
    assert [c for c in git.calls if c[0] == "switch"] == [("switch", "--create=fix/4-fix-the-thing", "origin/prep")]
    assert (saved(tmp_path)["step"], saved(tmp_path)["ticket"]) == ("pick", 4)


class FetchFails(Git):
    def __call__(self, *args):
        super().__call__(*args)
        if args[0] == "fetch":
            raise GiteaError("git fetch: no route")
        return ""


@pytest.mark.unit
def test_pick_fetches_origin_before_cutting_the_branch(tmp_path, gitea):
    backlog_four(gitea)
    git = Git()

    walk(tmp_path, Script("tickets", "#4", None, "stop"), gitea, git)

    kinds = [c[0] for c in git.calls]
    assert ("fetch", "origin") in git.calls
    assert kinds.index("fetch") < kinds.index("switch")


@pytest.mark.unit
def test_a_failed_fetch_cuts_no_branch_and_leaves_the_ticket(tmp_path, gitea):
    backlog_four(gitea)
    git = FetchFails()

    script = Script("tickets", "#4", None, "stop")

    walk(tmp_path, script, gitea, git)

    assert not [c for c in git.calls if c[0] == "switch"]
    assert gitea.column_of(4) == "Backlog"
    lines = [l for l in script.said if l.startswith("dp:")]
    assert len(lines) == 1 and "git fetch: no route" in lines[0]


class OldBranch(Git):
    """A repo where `fix/4-old` exists, merged into prep or not."""

    def __init__(self, merged):
        super().__init__()
        self.merged, self.gone = merged, False

    def __call__(self, *args):
        super().__call__(*args)
        if args[:2] == ("branch", "-d"):
            self.gone = True
        if args[:2] == ("branch", "--list"):
            return "  fix/4-old\n" if args[2] == "fix/4-old" and not self.gone else ""
        if args[:2] == ("branch", "--merged"):
            return "  fix/4-old\n" if self.merged and not self.gone else ""
        return " a.py | 2 +-" if args[0] == "diff" else ""


def backlog_four(gitea):
    gitea.add_issue(4, title="Old", labels=["TYPE/BUG"])
    gitea.put("Backlog", 4)


@pytest.mark.unit
def test_a_pick_over_an_old_branch_can_switch_to_it(tmp_path, gitea):
    backlog_four(gitea)
    git = OldBranch(merged=False)

    walk(tmp_path, Script("tickets", "#4", "fix/4-old", "Switch", "stop"), gitea, git)

    assert ("switch", "fix/4-old") in git.calls
    assert not [c for c in git.calls if c[0] == "switch" and c[1].startswith("--create")]
    assert gitea.column_of(4) == "In Progress"


@pytest.mark.unit
def test_a_pick_over_a_merged_branch_can_delete_it_and_start_new(tmp_path, gitea):
    backlog_four(gitea)
    git = OldBranch(merged=True)

    walk(tmp_path, Script("tickets", "#4", "fix/4-old", "Delete", "stop"), gitea, git)

    assert ("branch", "-d", "fix/4-old") in git.calls
    assert ("switch", "--create=fix/4-old", "origin/prep") in git.calls


@pytest.mark.unit
def test_an_unmerged_branch_is_not_offered_for_deletion(tmp_path, gitea):
    backlog_four(gitea)
    script = Script("tickets", "#4", "fix/4-old", "Switch", "stop")

    walk(tmp_path, script, gitea, OldBranch(merged=False))

    assert not [label for label in script.menus[1][0] if label.startswith("Delete")]


class CheckedOut(OldBranch):
    def __call__(self, *args):
        result = super().__call__(*args)
        return "fix/4-old\n" if args[:2] == ("branch", "--show-current") else result


@pytest.mark.unit
def test_the_checked_out_branch_is_not_offered_for_deletion(tmp_path, gitea):
    backlog_four(gitea)
    script = Script("tickets", "#4", "fix/4-old", "Switch", "stop")

    walk(tmp_path, script, gitea, CheckedOut(merged=True))

    assert not [label for label in script.menus[1][0] if label.startswith("Delete")]


@pytest.mark.unit
def test_a_pick_over_an_old_branch_can_name_a_new_one(tmp_path, gitea):
    backlog_four(gitea)
    git = OldBranch(merged=False)

    walk(tmp_path, Script("tickets", "#4", "fix/4-old", "Name", "fix/4-again", "stop"), gitea, git)

    assert ("switch", "--create=fix/4-again", "origin/prep") in git.calls
    assert ("branch", "-d", "fix/4-old") not in git.calls


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
def test_an_agent_step_prints_a_banner_before_and_a_next_line_after(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "pick", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("In Progress", 4)
    script = Script("check", "stop")

    walk(tmp_path, script, gitea)

    banner = next(line for line in script.said if "/exit returns to the guide" in line)
    assert banner.startswith("[ticket #4] Claude · ")
    assert script.said.index(banner) < script.said.index(
        "Step check of #4: read .factory/jobs/4/check.md and do it.")
    assert script.said[script.said.index("Step check of #4: read .factory/jobs/4/check.md and do it.") + 1] \
        == "Next: paste it into a session, then /exit and run dp guide"


@pytest.mark.unit
def test_a_human_step_says_what_to_do_next(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "pr", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Review", 4)
    script = Script("merge", True, "stop")

    walk(tmp_path, script, gitea)

    assert guide.NEXT_STEP in script.said


class OnBranch(Git):
    def __call__(self, *args):
        super().__call__(*args)
        return "feat/4-a-change\n" if args[:2] == ("branch", "--show-current") else ""


def at_merge(tmp_path, gitea, merged=None):
    """Ticket 4 at `merge`; its branch has a PR, merged or open, unless `merged` is None."""
    guide.write_state(tmp_path, {"flow": "ticket", "step": "pr", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Review", 4)
    if merged is not None:
        gitea.pulls.append({"number": 9, "head": {"ref": "feat/4-a-change"}, "merged": merged})


@pytest.mark.unit
def test_a_merged_pr_skips_the_done_question_at_merge(tmp_path, gitea):
    at_merge(tmp_path, gitea, merged=True)

    walk(tmp_path, Script("merge", "stop"), gitea, OnBranch())  # no confirm answer: merge must not ask

    assert saved(tmp_path)["step"] == "merge"


@pytest.mark.unit
def test_a_merged_pr_found_by_refs_skips_done_whatever_its_head_reads(tmp_path, gitea):
    at_merge(tmp_path, gitea)
    gitea.pulls.append({"number": 9, "head": {"ref": "refs/pull/9/head"}, "merged": True, "body": "Refs #4"})

    walk(tmp_path, Script("merge", "stop"), gitea, Git())  # git reads no branch; merge must not ask

    assert saved(tmp_path)["step"] == "merge"


@pytest.mark.unit
def test_a_pr_naming_the_ticket_second_on_its_refs_line_is_found(tmp_path, gitea):
    at_merge(tmp_path, gitea)
    gitea.pulls.append({"number": 9, "head": {"ref": "refs/pull/9/head"}, "merged": True, "body": "Refs #5 · #4"})

    walk(tmp_path, Script("merge", "stop"), gitea, Git())

    assert saved(tmp_path)["step"] == "merge"


@pytest.mark.unit
def test_the_newest_pr_that_refs_the_ticket_decides_at_merge(tmp_path, gitea):
    at_merge(tmp_path, gitea)
    gitea.pulls.append({"number": 8, "head": {"ref": "feat/4-a-change"}, "merged": False, "state": "closed",
                        "body": "Refs #4"})
    gitea.pulls.append({"number": 9, "head": {"ref": "refs/pull/9/head"}, "merged": True, "body": "Refs #4"})

    walk(tmp_path, Script("merge", "stop"), gitea, Git())

    assert saved(tmp_path)["step"] == "merge"


@pytest.mark.unit
def test_a_pr_with_no_refs_line_falls_back_to_the_branch_name(tmp_path, gitea):
    at_merge(tmp_path, gitea, merged=True)
    gitea.pulls.append({"number": 10, "head": {"ref": "other"}, "merged": False, "body": "Refs #5"})

    walk(tmp_path, Script("merge", "stop"), gitea, OnBranch())  # branch PR #9 is merged: no question

    assert saved(tmp_path)["step"] == "merge"


@pytest.mark.unit
def test_an_open_pr_keeps_the_walk_at_merge_and_says_so(tmp_path, gitea):
    at_merge(tmp_path, gitea, merged=False)
    script = Script("merge", "stop")

    walk(tmp_path, script, gitea, OnBranch())

    assert saved(tmp_path)["step"] == "pr"
    assert "[ticket #4] PR #9 is not merged · merge it, then run dp guide" in script.said


class MergesWhileMenuWaits(Script):
    """The person merges the PR in Gitea after the menu drew, before choosing."""

    def __init__(self, pull, *answers):
        super().__init__(*answers)
        self.pull = pull

    def choose(self, message, options, default=None):
        chosen = super().choose(message, options, default)
        self.pull["merged"] = True
        return chosen


@pytest.mark.unit
def test_a_pr_merged_while_the_menu_waits_passes_at_the_first_choice(tmp_path, gitea):
    at_merge(tmp_path, gitea, merged=False)
    script = MergesWhileMenuWaits(gitea.pulls[0], "merge", "stop")

    walk(tmp_path, script, gitea, OnBranch())

    assert saved(tmp_path)["step"] == "merge"
    assert not [line for line in script.said if "is not merged" in line]


class GiteaDropsAfterMenu(Script):
    """Gitea answers the menu's read, then goes unreachable."""

    def __init__(self, gitea, *answers):
        super().__init__(*answers)
        self.gitea = gitea

    def choose(self, message, options, default=None):
        chosen = super().choose(message, options, default)
        self.gitea.connection.call = mock.Mock(side_effect=GiteaError("unreachable"))
        return chosen


@pytest.mark.unit
def test_a_failed_reread_at_merge_keeps_the_menus_pr_state(tmp_path, gitea):
    at_merge(tmp_path, gitea, merged=True)
    script = GiteaDropsAfterMenu(gitea, "merge", "stop")  # no confirm answer: merged must still hold

    walk(tmp_path, script, gitea, OnBranch())

    assert saved(tmp_path)["step"] == "merge"


@pytest.mark.unit
def test_entering_merge_prints_the_prs_number_and_link(tmp_path, gitea):
    at_merge(tmp_path, gitea, merged=False)
    gitea.pulls[0]["html_url"] = "https://gitea.test/Org/Repo/pulls/9"
    script = Script("merge", "stop")

    walk(tmp_path, script, gitea, OnBranch())

    assert "PR #9 https://gitea.test/Org/Repo/pulls/9" in script.said


@pytest.mark.unit
def test_the_merge_choice_names_the_pr_it_found(tmp_path, gitea):
    at_merge(tmp_path, gitea, merged=False)
    script = Script("merge", "stop")

    walk(tmp_path, script, gitea, OnBranch())

    merge = next(label for label in script.menus[0][0] if label.startswith("merge"))
    assert merge.endswith("You merge PR #9 into prep once CI is green")


@pytest.mark.unit
def test_without_a_pr_the_merge_choice_and_output_stay_as_they_were(tmp_path, gitea):
    at_merge(tmp_path, gitea)
    script = Script("merge", True, "stop")

    walk(tmp_path, script, gitea, OnBranch())

    merge = next(label for label in script.menus[0][0] if label.startswith("merge"))
    assert merge.endswith("You merge the PR into prep once CI is green")
    assert not [line for line in script.said if line.startswith("PR #")]


@pytest.mark.unit
def test_the_merge_step_line_keeps_the_words_the_label_swaps_for_the_pr_number():
    flows_yaml = Path(guide.__file__).parents[3] / "flows.yaml"
    assert "You merge the PR into prep once CI is green" in flows_yaml.read_text(encoding="utf-8")


@pytest.mark.unit
def test_a_closed_unmerged_pr_is_not_told_to_merge(tmp_path, gitea):
    at_merge(tmp_path, gitea, merged=False)
    gitea.pulls[0]["state"] = "closed"
    script = Script("merge", "stop")

    walk(tmp_path, script, gitea, OnBranch())

    assert saved(tmp_path)["step"] == "pr"
    assert "[ticket #4] PR #9 is closed, not merged · reopen it or open a new one, then run dp guide" in script.said


class FailingGit(Git):
    def __call__(self, *args):
        raise GiteaError("git branch: not a git repository")


@pytest.mark.unit
def test_a_failing_git_at_merge_falls_back_to_asking_done(tmp_path, gitea):
    at_merge(tmp_path, gitea, merged=True)

    walk(tmp_path, Script("merge", True, "stop"), gitea, FailingGit())

    assert saved(tmp_path)["step"] == "merge"


@pytest.mark.unit
def test_without_a_pr_merge_asks_done_as_before(tmp_path, gitea):
    at_merge(tmp_path, gitea)

    walk(tmp_path, Script("merge", True, "stop"), gitea, OnBranch())

    assert saved(tmp_path)["step"] == "merge"


@pytest.mark.unit
def test_each_disposition_shows_its_effect(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "review", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("In Progress", 4)
    findings = tmp_path / ".factory" / "jobs" / "4" / "findings.json"
    findings.parent.mkdir(parents=True)
    findings.write_text(json.dumps([
        {"id": "S1", "file": "a.py", "line": 3, "severity": "low", "finding": "Too long"}]))
    script = Script("Defer", "fix", "stop")

    walk(tmp_path, script, gitea)

    labels = script.menus[0][0]
    assert "Defer     opens a new Triage ticket" in labels
    assert "Fix       goes to the fix step" in labels


@pytest.mark.unit
def test_stop_shows_its_effect(tmp_path, gitea):
    script = Script("stop")

    walk(tmp_path, script, gitea)

    assert "stop        saves the position and exits" in script.menus[0][0]


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
def test_a_ticket_placed_at_build_by_the_board_is_offered_build_first(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "pick", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("In Progress", 4)
    script = Script("build", "stop")

    walk(tmp_path, script, gitea)

    assert script.menus[0][0][0].startswith("build  ")
    assert script.menus[1][0][0].startswith("check  ")
    assert (tmp_path / ".factory" / "jobs" / "4" / "build.md").is_file()


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
    script = Script("retro", "stop")

    walk(tmp_path, script, None)

    assert "Type /datumpin:retro in the session you worked in." in script.said
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
    script = Script("tickets", "#4", None, "stop")

    walk(tmp_path, script, gitea)

    assert ("milestone", 4, 3) in gitea.writes
    assert "[ticket #4] joined v1" in script.said


@pytest.mark.unit
def test_sign_off_shows_the_recorded_dispositions_and_asks_only_done(tmp_path):
    guide.write_state(tmp_path, {"flow": "release", "step": "release-pr", "ticket": None})
    findings = tmp_path / ".factory" / "jobs" / "release" / "findings.json"
    findings.parent.mkdir(parents=True)
    findings.write_text(json.dumps([
        {"id": "S1", "file": "a.py", "line": 3, "severity": "low", "finding": "Long", "disposition": "Fixed (abc123)"},
        {"id": "P1", "file": "b.py", "line": 9, "severity": "medium", "finding": "Odd",
         "disposition": "Dismissed: out of scope"}]))
    script = Script("sign-off", True, "stop")  # one confirm: Done?, no disposition question

    walk(tmp_path, script, None)

    assert "[release] S1 Fixed (abc123)" in script.said
    assert "[release] P1 Dismissed: out of scope" in script.said
    assert saved(tmp_path)["step"] == "sign-off"


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
    assert labels == ["finish", "defect", "───────────", "board", "flows…", "pause", "stop"]  # no gate: #5 is not tested


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
def test_gate_moves_every_tested_ticket_of_the_milestone_to_dod(gitea):
    gitea.add_issue(4, milestone="v1", comments=[pointer_tested(4)])
    gitea.add_issue(5, milestone="v1", comments=[pointer_tested(5)])
    gitea.add_issue(6, milestone="v2")
    gitea.put("Testing", 4, 5, 6)

    moved = guide.gate(gitea.connection, "v1")

    assert moved == [4, 5]
    assert gitea.column_of(4) == gitea.column_of(5) == "DoD"
    assert gitea.column_of(6) == "Testing"


@pytest.mark.unit
def test_gate_lists_the_untested_and_moves_none(gitea):
    gitea.add_issue(4, milestone="v1", comments=[pointer_tested(4)])
    gitea.add_issue(5, milestone="v1")
    gitea.put("Testing", 4, 5)

    with pytest.raises(GiteaError, match="#5"):
        guide.gate(gitea.connection, "v1")

    assert gitea.column_of(4) == "Testing"


@pytest.mark.unit
def test_tag_refuses_while_the_release_pr_is_not_merged_on_main(gitea):
    gitea.pulls.append({"number": 30, "base": {"ref": "main"}, "head": {"ref": "prep"}, "merged": False, "state": "open", "title": "v1.0.0 – first"})
    git = Git()

    with pytest.raises(GiteaError, match="#30"):
        guide.tag(gitea.connection, git, Script(), "v1.0.0")

    assert not [call for call in git.calls if call[0] in ("tag", "push")]


@pytest.mark.unit
def test_tag_tags_main_and_pushes_the_tag_after_a_confirm(gitea):
    gitea.pulls.append({"number": 30, "base": {"ref": "main"}, "head": {"ref": "prep"}, "merged": True, "title": "v1.0.0 – first"})
    git = Git()

    tagged = guide.tag(gitea.connection, git, Script(True), "v1.0.0")

    assert tagged is True
    assert ("tag", "v1.0.0", "origin/main") in git.calls
    assert git.calls[-1] == ("push", "origin", "v1.0.0")


@pytest.mark.unit
def test_tag_ignores_other_prs_into_main(gitea):
    gitea.pulls.append({"number": 30, "base": {"ref": "main"}, "head": {"ref": "prep"}, "merged": True, "title": "v1.0.0 – first"})
    gitea.pulls.append({"number": 31, "base": {"ref": "main"}, "head": {"ref": "hotfix"}, "merged": False, "title": "Hotfix"})

    assert guide.tag(gitea.connection, Git(), Script(True), "v1.0.0") is True
    with pytest.raises(GiteaError, match="for v1.0.1"):
        guide.tag(gitea.connection, Git(), Script(True), "v1.0.1")


@pytest.mark.unit
@pytest.mark.parametrize("version", ["v1", "-f", "1.0.0"])
def test_tag_rejects_a_version_that_is_not_vxyz(gitea, version):
    git = Git()

    with pytest.raises(GiteaError, match="not a vX.Y.Z"):
        guide.tag(gitea.connection, git, Script(True), version)

    assert not git.calls


@pytest.mark.unit
def test_tag_does_nothing_when_the_confirm_is_declined(gitea):
    gitea.pulls.append({"number": 30, "base": {"ref": "main"}, "head": {"ref": "prep"}, "merged": True, "title": "v1.0.0 – first"})
    git = Git()

    assert guide.tag(gitea.connection, git, Script(False), "v1.0.0") is False
    assert not [call for call in git.calls if call[0] in ("tag", "push")]


@pytest.mark.unit
def test_gate_waits_for_a_pointer_on_a_ticket_closed_into_dod(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4, milestone="v1")
    gitea.add_issue(5, milestone="v1", state="closed")  # closed by hand, never tested
    gitea.put("Testing", 4)
    gitea.put("DoD", 5)
    script = Script("stop")

    walk(tmp_path, script, gitea)

    assert "gate" not in [label.split()[0] for label in script.menus[0][0]]


@pytest.mark.unit
def test_gate_is_offered_when_a_closed_ticket_in_dod_has_its_pointer(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4, milestone="v1")
    gitea.add_issue(5, milestone="v1", state="closed", comments=[pointer_tested(5)])
    gitea.put("Testing", 4)
    gitea.put("DoD", 5)
    script = Script("stop")

    walk(tmp_path, script, gitea)

    assert "gate" in [label.split()[0] for label in script.menus[0][0]]


@pytest.mark.unit
def test_leaving_test_posts_a_pointer_tested(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Testing", 4)

    walk(tmp_path, Script("finish", "laptop, names end -dev", "stop"), gitea)

    posted = [w for w in gitea.writes if w[0] == "comment"]
    assert len(posted) == 1
    assert posted[0][2].startswith("Tested by hand, ")
    assert posted[0][2].endswith(". Done: laptop, names end -dev. → #4")


@pytest.mark.unit
def test_a_ticket_with_a_pointer_is_not_asked_tested_ok_again(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4, comments=[pointer_tested(4)])
    gitea.put("Testing", 4)


    assert [w for w in gitea.writes if w[0] == "comment"] == []


@pytest.mark.unit
def test_a_defect_after_the_pointer_asks_tested_ok_again(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4, comments=[pointer_tested(4), ("Squire", "Defect at test, 2026-10-23. Left: x. → Backlog")])
    gitea.put("Testing", 4)

    walk(tmp_path, Script("board", True, "laptop", "stop"), gitea)

    assert len([w for w in gitea.writes if w[0] == "comment"]) == 1


@pytest.mark.unit
def test_leaving_test_posts_one_pointer(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4)
    gitea.add_issue(6)
    gitea.put("Testing", 4)
    gitea.put("Backlog", 6)

    script = Script("board", True, "laptop", "stop")
    script.job = lambda *args: None
    walk(tmp_path, script, gitea)

    assert len([w for w in gitea.writes if w[0] == "comment"]) == 1


@pytest.mark.unit
def test_finish_posts_the_pointer_closes_the_ticket_and_lands_on_the_home_menu(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Testing", 4)
    script = Script("finish", "laptop", "stop")

    walk(tmp_path, script, gitea)

    assert [w[0] for w in gitea.writes if w[0] in ("comment", "close")] == ["comment", "close"]
    assert gitea.issues[4]["state"] == "closed"
    assert gitea.column_of(4) == "DoD"
    assert "[ticket #4] DONE · closed, in DoD" in script.said
    assert [label.split()[0] for label in script.menus[1][0]] == HOME
    assert saved(tmp_path)["ticket"] is None


@pytest.mark.unit
def test_a_defect_reopens_the_ticket_to_backlog_with_a_progress_comment(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Testing", 4)

    walk(tmp_path, Script("defect", "login fails", "stop"), gitea)  # no Tested OK? answer: a defect is not tested

    comment = next(w for w in gitea.writes if w[0] == "comment")
    assert comment[2].endswith(". Landed: merged to prep. Left: login fails. → Backlog")
    assert gitea.column_of(4) == "Backlog"
    assert gitea.issues[4]["state"] == "open"


@pytest.mark.unit
def test_finish_prints_the_column_the_ticket_is_in(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.lands_in = "Done"  # something moved the card on, as board-sync did
    gitea.add_issue(4)
    gitea.put("Testing", 4)
    script = Script("finish", "laptop", "stop")

    walk(tmp_path, script, gitea)

    assert "[ticket #4] DONE · closed, in Done" in script.said


@pytest.mark.unit
def test_finish_prints_dod_when_the_card_stays_there(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Testing", 4)
    script = Script("finish", "laptop", "stop")

    walk(tmp_path, script, gitea)

    assert "[ticket #4] DONE · closed, in DoD" in script.said


@pytest.mark.unit
def test_finish_prints_no_column_when_the_card_is_off_the_board(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Testing", 4)
    script = Script("finish", "laptop", "stop")

    with mock.patch.object(guide.commands, "finish", return_value=None):
        walk(tmp_path, script, gitea)

    assert "[ticket #4] DONE · closed, in no column" in script.said


@pytest.mark.unit
def test_an_untested_change_is_not_finished(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Testing", 4)

    walk(tmp_path, Script("board", False, "stop"), gitea)

    assert gitea.issues[4]["state"] == "open"
    assert saved(tmp_path)["step"] == "test"


@pytest.mark.unit
def test_entering_test_asks_nothing_and_says_leaving_records_tested(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "merge", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Review", 4)
    script = Script("test", "stop")  # no confirm answer: entering test must not ask

    walk(tmp_path, script, gitea)

    assert saved(tmp_path)["step"] == "test"
    assert guide.LEAVING_TEST in script.said


@pytest.mark.unit
def test_an_untested_change_stays_at_test(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Testing", 4)
    script = Script("board", False, "stop")

    walk(tmp_path, script, gitea)

    assert not [w for w in gitea.writes if w[0] == "comment"]
    assert saved(tmp_path)["step"] == "test"
    assert "[ticket #4] not tested · staying at test" in script.said


@pytest.mark.unit
def test_leaving_the_ticket_flow_holds_the_ticket_and_the_home_menu_resumes_it(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4, comments=[pointer_tested(4)])
    gitea.put("Testing", 4)
    script = Script("flows…", "align", "stop")  # the Pointer is already posted: no "Tested OK?"

    walk(tmp_path, script, gitea)

    assert saved(tmp_path)["flow"] == "align"
    assert saved(tmp_path)["paused"] == [{"flow": "ticket", "step": "test", "ticket": 4}]

    guide.write_state(tmp_path, None, saved(tmp_path)["paused"])
    script = Script("resume…", "#4", "stop")
    walk(tmp_path, script, gitea)

    assert "resume…     Continue a paused ticket" in script.menus[0][0]
    assert "#4 at test" in script.menus[1][0]
    assert (saved(tmp_path)["flow"], saved(tmp_path)["step"], saved(tmp_path)["ticket"]) == ("ticket", "test", 4)
    assert saved(tmp_path)["paused"] == []


@pytest.mark.unit
def test_pause_saves_the_step_and_lands_on_the_home_menu_without_asking_tested_ok(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Testing", 4)
    script = Script("pause", "stop")

    walk(tmp_path, script, gitea)

    assert "pause       Saves this ticket's step, returns to the home menu" in script.menus[0][0]
    assert "[ticket #4] paused · test · home menu" in script.said
    assert [label.split()[0] for label in script.menus[1][0]] == [*HOME[:1], "resume…", *HOME[1:]]
    assert saved(tmp_path)["ticket"] is None
    assert saved(tmp_path)["paused"] == [{"flow": "ticket", "step": "test", "ticket": 4}]
    assert not [w for w in gitea.writes if w[0] == "comment"]


@pytest.mark.unit
def test_more_than_one_paused_ticket_is_held_each_with_its_step(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "build", "ticket": 5},
                      [{"flow": "ticket", "step": "test", "ticket": 4}])
    gitea.add_issue(4)
    gitea.add_issue(5)
    gitea.put("Testing", 4)
    gitea.put("In Progress", 5)
    script = Script("pause", "resume…", "#4", "stop")

    walk(tmp_path, script, gitea)

    assert script.menus[2][0][:2] == ["#4 at test", "#5 at build"]
    assert saved(tmp_path)["ticket"] == 4
    assert saved(tmp_path)["paused"] == [{"flow": "ticket", "step": "build", "ticket": 5}]


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
def test_the_end_of_a_flow_is_the_home_menu(tmp_path):
    guide.write_state(tmp_path, {"flow": "session", "step": "handoff", "ticket": None})
    script = Script("stop")

    walk(tmp_path, script, None)

    assert [label.split()[0] for label in script.menus[0][0]] == HOME


@pytest.mark.unit
def test_end_session_runs_retro_then_handoff(tmp_path):
    script = Script("end", "stop")

    walk(tmp_path, script, None)

    assert (saved(tmp_path)["flow"], saved(tmp_path)["step"]) == ("session", "retro")
    assert script.menus[1][0][0].startswith("handoff")


@pytest.mark.unit
def test_handoff_prints_how_to_start_the_new_chat(tmp_path):
    guide.write_state(tmp_path, {"flow": "session", "step": "retro", "ticket": None})
    script = Script("handoff", "stop")

    walk(tmp_path, script, None)

    assert guide.NEW_CHAT in script.said


@pytest.mark.unit
def test_flows_menu_leaves_out_ticket_and_session(tmp_path):
    script = Script("flows…", "back", "stop")

    walk(tmp_path, script, None)

    assert [label.split()[0] for label in script.menus[1][0]] == ["release", "align", "deploy", "back"]


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
@pytest.mark.parametrize("step", ["fix", "release-pr"])
def test_the_later_release_briefs_carry_the_promotion_diff(tmp_path, gitea, step):
    guide.write_state(tmp_path, {"flow": "release", "step": "review", "ticket": None})

    walk(tmp_path, Script(step, "stop"), gitea, Promotion(" b.py | 9 +"))

    text = (tmp_path / ".factory" / "jobs" / "release" / f"{step}.md").read_text(encoding="utf-8")
    assert "b.py | 9 +" in text


@pytest.mark.unit
def test_an_empty_promotion_diff_fails_the_review(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "release", "step": "gate", "ticket": None})

    with pytest.raises(GiteaError, match="empty diff origin/main...prep"):
        walk(tmp_path, Script("review", "stop"), gitea, Promotion(""))

    assert not (tmp_path / ".factory" / "jobs" / "release").exists()
    assert saved(tmp_path)["step"] == "gate"


@pytest.mark.unit
def test_a_git_error_on_the_promotion_diff_is_not_an_empty_diff(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "release", "step": "gate", "ticket": None})

    def no_main(*args):
        raise GiteaError("git diff: unknown revision origin/main")

    with pytest.raises(GiteaError, match="unknown revision"):
        walk(tmp_path, Script("review", "stop"), gitea, no_main)


@pytest.mark.unit
def test_finish_asks_the_evidence_once_and_no_tested_confirm(tmp_path, gitea):
    guide.write_state(tmp_path, {"flow": "ticket", "step": "test", "ticket": 4})
    gitea.add_issue(4)
    gitea.put("Testing", 4)
    script = Script("finish", "laptop", "stop")  # a confirm prompt would consume "laptop" and fail

    walk(tmp_path, script, gitea)

    assert gitea.issues[4]["state"] == "closed"


@pytest.mark.unit
def test_the_gate_step_runs_dp_gate_without_an_agent_session(tmp_path, gitea):
    gitea.milestones.append({"id": 7, "title": "v1", "due_on": None})
    gitea.add_issue(4, milestone="v1", comments=[pointer_tested(4)])
    gitea.put("Testing", 4)
    script = Script(None)  # the milestone, by default the open one due first

    reached = guide.run(tmp_path, guide.flows.load(), None, {"flow": "release", "step": "gate"},
                        script, gitea.connection, Git())

    assert reached == {"flow": "release", "step": "gate", "ticket": None}
    assert gitea.column_of(4) == "DoD"
    assert not (tmp_path / ".factory" / "jobs").exists()


@pytest.mark.unit
def test_the_tag_step_runs_dp_tag_without_an_agent_session(tmp_path, gitea):
    gitea.milestones.append({"id": 7, "title": "v1.0.0", "due_on": None})
    gitea.pulls.append({"number": 30, "base": {"ref": "main"}, "head": {"ref": "prep"}, "merged": True, "title": "v1.0.0 – first"})
    git = Git()

    reached = guide.run(tmp_path, guide.flows.load(), None, {"flow": "release", "step": "tag"},
                        Script(None, True), gitea.connection, git)

    assert reached["step"] == "tag"
    assert git.calls[-1] == ("push", "origin", "v1.0.0")
    assert not (tmp_path / ".factory" / "jobs").exists()


@pytest.mark.unit
def test_handoff_tells_the_user_to_run_dp_guide_not_to_paste_a_prompt():
    assert "dp guide" in guide.NEW_CHAT
    assert "paste" not in guide.NEW_CHAT
