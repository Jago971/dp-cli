"""Unit tier: dp guide's look at a terminal (dp.terminal), rendered to text."""
import contextlib
import contextlib
import io
import re
from pathlib import Path

import pytest
from rich.console import Console

from dp import terminal


@pytest.fixture
def screen(monkeypatch):
    """A Terminal printing to a string, in true colour, with no clipboard tool."""
    monkeypatch.setattr(terminal.shutil, "which", lambda name: None)
    shown = terminal.Terminal()
    shown.console = Console(file=io.StringIO(), force_terminal=True, color_system="truecolor", width=200)
    return shown


def output(shown):
    return shown.console.file.getvalue()


def styles_at(text, word):
    start = text.plain.index(word)
    return [str(span.style) for span in text.spans if span.start <= start < span.end]


@pytest.mark.unit
def test_a_log_line_mutes_its_ref_and_colours_only_a_failure():
    text = terminal.log_line("[ticket #4] check · FAILED · tests red")

    assert terminal.MUTED in styles_at(text, "#4")
    assert f"bold {terminal.RED}" in styles_at(text, "FAILED")
    assert styles_at(text, "check") == []
    assert styles_at(terminal.log_line("[ticket #4] check · DONE"), "DONE") == []


@pytest.mark.unit
def test_the_header_shows_the_position_and_only_the_current_step_in_colour(screen):
    screen.header({"flow": "ticket", "step": "build", "ticket": 4}, "dev",
                  [("pick", "done"), ("build", "current"), ("check", "next")], "Agree the seams, then build")

    shown = re.sub(r"\x1b\[[0-9;]*m", "", output(screen))
    assert " dp  guide  ticket flow · #4 · build (dev)" in shown
    assert "✓ pick ─ ● build ─ ○ check\n Agree the seams, then build\n" in shown
    assert output(screen).count("38;2;224;25;125") == 1  # pink, on the current step only
    assert "38;2;0;181;204" not in output(screen)  # no cyan outside the menu


@pytest.mark.unit
def test_a_job_prompt_without_a_clipboard_tool_is_only_shown(screen):
    screen.job("Step check of #4: read .factory/jobs/4/check.md and do it.", None, None)

    assert "Step check of #4" in output(screen)
    assert "copied" not in output(screen)


@pytest.mark.unit
def test_no_color_drops_the_colour(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    shown = terminal.Terminal()
    shown.console = Console(file=io.StringIO(), force_terminal=True, color_system="truecolor")

    shown.say("[ticket #4] check · DONE")

    assert "\x1b[38;2" not in output(shown)


@pytest.mark.unit
def test_claude_starts_on_the_steps_model_and_effort(monkeypatch):
    monkeypatch.setattr(terminal.shutil, "which", lambda name: "/bin/claude" if name == "claude" else None)

    assert terminal.claude_command("Step x", "opus", "high") == [
        "/bin/claude", "--model", "opus", "--effort", "high", "Step x"]
    assert terminal.claude_command("Step x", None, None) == ["/bin/claude", "Step x"]


@pytest.mark.unit
def test_claude_inside_the_repo_is_not_run(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(terminal.shutil, "which", lambda name: str(tmp_path / "claude.cmd"))

    assert terminal.claude_command("Step x", None, None) is None


@pytest.mark.unit
def test_without_claude_the_panel_names_the_model_to_use(screen):
    screen.job("Step shape of #4: read .factory/jobs/4/shape.md and do it.", "opus", "high")

    assert "use opus · high first" in output(screen)


def board(*columns):
    return {"repo": "Org/Repo", "pulls": [], "milestones": [], "unsorted": [],
            "columns": [{"title": title, "tickets": tickets} for title, tickets in columns]}


def ticket(number, labels=()):
    return {"number": number, "title": f"Ticket {number}", "labels": list(labels), "milestone": None}


@pytest.mark.unit
def test_the_board_colours_only_what_you_act_on_and_what_is_stuck(screen):
    screen.console.print(terminal.board_view(board(
        ("Backlog", [ticket(1, ["STATUS/BLOCKED"])]), ("In Progress", [ticket(2)]))))

    shown = output(screen)
    assert shown.count("38;2;224;25;125") == 1  # pink: the In Progress ticket
    assert shown.count("38;2;249;216;0") == 1  # yellow: the STATUS label
    assert "Ticket 1" in shown and "Ticket 2" in shown


@pytest.mark.unit
def test_a_long_board_column_lists_numbers_only(screen):
    screen.console.print(terminal.board_view(board(("Backlog", [ticket(n) for n in range(1, 10)]))))

    shown = re.sub(r"\x1b\[[0-9;]*m", "", output(screen))
    assert "#1 #2 #3" in shown and "Ticket 1" not in shown


@pytest.mark.unit
def test_only_the_terminal_module_styles_output():
    sources = (Path(terminal.__file__).parent).glob("*.py")

    styling = [s.name for s in sources if s.name != "terminal.py"
               and re.search(r"^\s*(import|from)\s+(rich|questionary)\b", s.read_text(encoding="utf-8"), re.M)]
    assert styling == []


@pytest.mark.unit
def test_plain_drops_spinners_and_menu_colour(monkeypatch):
    monkeypatch.setattr(terminal, "plain", True)

    assert isinstance(terminal.busy("Reading the board"), contextlib.nullcontext)
    assert terminal.menu_look(terminal.MENU) == {"style": None, "color_depth": terminal.ColorDepth.DEPTH_1_BIT}


@pytest.mark.unit
def test_a_done_line_is_written_as_it_is(monkeypatch):
    shown = Console(file=io.StringIO(), force_terminal=True, color_system="truecolor")
    monkeypatch.setattr(terminal, "console", lambda stderr=False: shown)

    terminal.done("#4 Fix the FAILED build")

    assert shown.file.getvalue() == "✔ #4 Fix the FAILED build\n"
