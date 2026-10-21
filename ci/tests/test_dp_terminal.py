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
