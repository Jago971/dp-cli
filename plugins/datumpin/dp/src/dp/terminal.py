"""dp's look: the one module that styles output, with colour only where it directs the eye.

Summary: say, done and failed lines, busy spinners and the board table for
         the commands; Terminal, the guide's prompts (guide.Plain), for
         `dp guide`.
Input:   what the commands and dp.guide show and ask; `dp --plain`
         (use_plain) for plain text.
Output:  Rich lines, tables, panels and spinners, and questionary menus.
         NO_COLOR, `--plain` and output that is not a terminal give the same
         text unstyled and without spinners; a terminal without true colour
         gets the nearest colours it has. An agent step starts Claude Code in
         this terminal on the step's model and effort; without `claude` on the
         PATH, its Job prompt shows in a panel, copied to the clipboard when
         the system has a tool for it.
"""
import contextlib
import os
import re
import shutil
import subprocess
import sys

import questionary
from rich import box
from rich.console import Console
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from dp import guide

# Each colour means one thing, from the DP palette (AHJ instances/dp/branding/
# theme.css); the rest is the terminal's own text, or its own grey to recede.
PINK = "#e0197d"  # you are here, act now: the current step, a question, the Job prompt
CYAN = "#00b5cc"  # the cursor: the highlighted menu row
YELLOW = "#f9d800"  # attention: a correction, Gitea unreachable, a gate
RED = "#c0392b"  # failure
MUTED = "bright_black"  # the terminal theme's grey, for what supports the main text
OUTCOMES = {"FAILED": RED, "BLOCKED": RED, "CHANGES": YELLOW}
SEVERITIES = {"high": RED, "medium": YELLOW}
MARKS = {"done": "✓", "current": "●", "next": "○"}
CLIPBOARDS = (["clip"], ["pbcopy"], ["wl-copy"], ["xclip", "-selection", "clipboard"])
REF = re.compile(r"\[[^\]]+\]")
SHORTCUTS = 36  # questionary's limit for number and letter shortcuts
FULL_COLUMN = 8  # a longer board column lists numbers only, as the formats Board view
ACTING = "In Progress"  # the board column whose tickets you act on, in pink
ATTENTION = "STATUS/"  # a label that says why a ticket cannot move, in yellow
plain = False  # set by `dp --plain`

MENU = questionary.Style([
    ("qmark", f"fg:{PINK} bold"), ("question", "bold"), ("pointer", f"fg:{CYAN} bold"),
    ("highlighted", f"fg:{CYAN} bold"), ("answer", "bold"), ("instruction", "fg:ansibrightblack")])
GATE = questionary.Style([("qmark", f"fg:{YELLOW} bold"), ("question", "bold"), ("answer", "bold")])


def log_line(line, colour=""):
    """A Log line (formats): its ref and separators recede; a failure or a change stands out."""
    text = Text(line, style=colour)
    found = REF.match(line)
    if found:
        text.stylize(MUTED, *found.span())
    text.highlight_regex(r" · ", MUTED)
    for word, outcome in OUTCOMES.items():
        text.highlight_words([word], f"bold {outcome}")
    return text


def use_plain(on):
    """No colour and no spinners when on: `dp --plain`, for logs."""
    global plain
    plain = on


def at_terminal():
    # Both ends: on Windows a null stdin (NUL) passes isatty().
    return sys.stdin.isatty() and sys.stdout.isatty()


def console(stderr=False):
    # NO_COLOR and --plain drop every style, bold included, as output that is not a terminal does.
    unstyled = plain or bool(os.environ.get("NO_COLOR"))
    return Console(highlight=False, soft_wrap=True, stderr=stderr, force_terminal=False if unstyled else None)


def say(*lines):
    out = console()
    for line in lines:
        out.print(line, markup=False)


def done(*lines):
    """A finished write, one line each: `✔ <what happened>`."""
    out = console()
    for line in lines:
        out.print(Text("✔ ") + log_line(line))


def failed(line):
    """A failure, on stderr: `✖ <what failed>`."""
    console(stderr=True).print(Text("✖ ", style=f"bold {RED}") + Text(line))


def busy(message, quiet=False):
    """A spinner while Gitea answers; none when quiet (JSON), plain or not at a terminal."""
    if quiet or plain:
        return contextlib.nullcontext()
    return console().status(Text(f"{message}…", style=MUTED), spinner="dots", spinner_style=MUTED)


def ticket_text(ticket, column):
    """A ticket on the board: its number and title, pink when you act on it; its labels and milestone muted,
    but a STATUS label in yellow."""
    text = Text(f"#{ticket['number']} {ticket['title']}", style=PINK if column == ACTING else "")
    for label in ticket["labels"]:
        text.append(" · ", MUTED).append(label, YELLOW if label.startswith(ATTENTION) else MUTED)
    if ticket["milestone"]:
        text.append(" · ", MUTED).append(ticket["milestone"], MUTED)
    return text


def board_view(board):
    """The Board as a table, one row per column, then its milestones and PRs."""
    table = Table(box=None, show_header=False, padding=(0, 2, 0, 0))
    table.add_column(style="bold", no_wrap=True)
    table.add_column(justify="right", style=MUTED)
    table.add_column()
    for column in board["columns"] + [{"title": "Unsorted", "tickets": board["unsorted"]}]:
        tickets = column["tickets"]
        if len(tickets) > FULL_COLUMN:
            cell = Text(" ".join(f"#{t['number']}" for t in tickets),
                        style=PINK if column["title"] == ACTING else "")
        else:
            cell = Text("\n").join(ticket_text(t, column["title"]) for t in tickets)
        table.add_row(column["title"], str(len(tickets)), cell)
    lines = [Text(f"{board['repo']} · {len(board['pulls'])} PR", style="bold"), table]
    lines += [Text.assemble(("Milestone  ", MUTED), m["title"],
                            (f" · {m['closed']} of {m['open'] + m['closed']} closed", MUTED))
              for m in board["milestones"]]
    lines += [Text.assemble(("PR  ", MUTED), f"#{p['number']} {p['title']}", (f" · {p['head']} → {p['base']}", MUTED))
              for p in board["pulls"]]
    return Group(*lines)


def show_board(board):
    console().print(board_view(board))


def claude_command(prompt, model, effort):
    """The command that starts Claude Code on the prompt, or None without `claude` on the PATH."""
    claude = shutil.which("claude")
    if not claude:
        return None
    return [claude, *(["--model", model] if model else []), *(["--effort", effort] if effort else []), prompt]


def copy(text):
    """Put text on the clipboard with the system's tool; False when there is none or it fails."""
    command = next((c for c in CLIPBOARDS if shutil.which(c[0])), None)
    if not command:
        return False
    try:
        return subprocess.run(command, input=text, text=True, capture_output=True, timeout=5).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


class Terminal(guide.Plain):
    """The guide's prompts at a terminal; Ctrl-C raises KeyboardInterrupt."""

    def __init__(self):
        self.console = console()

    def say(self, line):
        self.console.print(log_line(line))

    def note(self, line):
        self.console.print(log_line(line, YELLOW))

    def outro(self, line):
        self.console.print(Text("└ ", style=MUTED) + log_line(line))

    def header(self, position, env, rail, does):
        line = Text.assemble((" dp ", f"bold #ffffff on {PINK}"), (" guide  ", MUTED))
        if not position:
            line.append("start")
        else:
            line.append(f"{position['flow']} flow")
            if position["ticket"]:
                line.append(" · ", MUTED).append(f"#{position['ticket']}")
            line.append(" · ", MUTED).append(position["step"], "bold").append(f" ({env})", MUTED)
        self.console.print()
        self.console.print(line)
        if rail:
            steps = [Text(f"{MARKS[state]} {step}", style=f"bold {PINK}" if state == "current" else MUTED)
                     for step, state in rail]
            self.console.print(Text(" ").append(Text(" ─ ", style=MUTED).join(steps)))
        if does:
            self.console.print(f" {does}", markup=False)
        self.console.print()

    def job(self, prompt, model, effort):
        model_label = " · ".join(filter(None, [model, effort]))
        command = claude_command(prompt, model, effort)
        if command:
            self.console.print(Text.assemble(("◆ ", f"bold {PINK}"), ("Claude", "bold"),
                                             (f" · {model_label or 'the session model'}", MUTED),
                                             (" · exit to come back", MUTED)))
            subprocess.run(command)
            return
        copied = copy(prompt)
        hint = (f"use {model_label} first" if model_label else "runs on the session's model") \
            + (" · copied to the clipboard" if copied else "")
        self.console.print(Panel(Text(prompt, style="bold"), box=box.ROUNDED, border_style=PINK, expand=False,
                                 title="paste into a session", title_align="left",
                                 subtitle=Text(hint, style=MUTED), subtitle_align="right"))

    def finding(self, finding):
        self.console.print(Text.assemble(
            (finding["id"], "bold"), " ", (finding["severity"], SEVERITIES.get(finding["severity"], MUTED)),
            " ", (f"{finding['file']}:{finding['line']}", MUTED), " ", finding["finding"]))

    def busy(self, message):
        return busy(message)

    def choose(self, message, options, default=None):
        # Plain titles, so questionary marks the cursor's row in cyan.
        rows = [questionary.Separator(f"  {label}") if value == guide.SEPARATOR_VALUE
                else questionary.Choice(label, value=n) for n, (label, value) in enumerate(options)]
        preselected = next((row for row, (_, value) in zip(rows, options)
                            if default is not None and value is default), None)
        index = questionary.select(
            message, rows, default=preselected, qmark="◆", pointer="❯", style=MENU,
            use_shortcuts=len(rows) <= SHORTCUTS, instruction="(arrows or a number)").unsafe_ask()
        return options[index][1]

    def confirm(self, message):
        return questionary.confirm(message, qmark="◆", style=GATE).unsafe_ask()

    def text(self, message, default):
        return questionary.text(message, default=default, qmark="◆", style=MENU).unsafe_ask()
