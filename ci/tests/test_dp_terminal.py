"""Unit tier: dp guide's look at a terminal (dp.terminal), rendered to text."""
import io
import re

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
def test_a_log_line_colours_its_ref_and_outcome():
    text = terminal.log_line("[ticket #4] check · FAILED · tests red")

    assert terminal.CYAN in styles_at(text, "ticket")
    assert terminal.PINK in styles_at(text, "#4")
    assert f"bold {terminal.RED}" in styles_at(text, "FAILED")


@pytest.mark.unit
def test_a_menu_row_splits_the_name_its_line_and_a_fork():
    assert terminal.title("gate        Move the tickets → release flow") == [
        ("class:name", "gate"), ("class:does", "        Move the tickets"), ("class:fork", " → release flow")]
    assert terminal.title("#4 A ticket")[0] == ("class:ticket", "#4")


@pytest.mark.unit
def test_the_header_shows_the_position_and_the_rail(screen):
    screen.header({"flow": "ticket", "step": "build", "ticket": 4}, "dev",
                  [("pick", "done"), ("build", "current"), ("check", "next")])

    shown = re.sub(r"\x1b\[[0-9;]*m", "", output(screen))
    assert " dp  guide   ticket flow · #4 · build  dev" in shown
    assert "✓ pick ─ ● build ─ ○ check" in shown
    assert "\x1b[38;2;0;181;204m" in output(screen)  # cyan, in true colour


@pytest.mark.unit
def test_a_job_prompt_without_a_clipboard_tool_is_only_shown(screen):
    screen.job("Step check of #4: read .factory/jobs/4/check.md and do it.")

    assert "Step check of #4" in output(screen)
    assert "copied" not in output(screen)


@pytest.mark.unit
def test_no_color_drops_the_colour(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    shown = terminal.Terminal()
    shown.console = Console(file=io.StringIO(), force_terminal=True, color_system="truecolor")

    shown.say("[ticket #4] check · DONE")

    assert "\x1b[38;2" not in output(shown)
