"""dp guide's look at a terminal: the DP palette, the rail, the menus and the Job prompt panel.

Summary: Terminal, the guide's prompts (guide.Plain) in colour.
Input:   what dp.guide asks and shows.
Output:  Rich lines, panels and spinners, and questionary menus. Colour
         follows NO_COLOR, and a terminal without true colour gets the
         nearest it has. A Job prompt is also copied to the clipboard when the
         system has a tool for it.
"""
import re
import shutil
import subprocess

import questionary
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from dp import guide

# The DP palette (AHJ instances/dp/branding/theme.css), without its navy, which a
# dark terminal hides. Cyan is structure (about half), pink is focus (about a
# third), yellow is attention (the rest); grey mutes, red fails.
CYAN, PINK, YELLOW, GREY, RED = "#00b5cc", "#e0197d", "#f9d800", "#a8b8c8", "#c0392b"
OUTCOMES = {"DONE": CYAN, "PASS": CYAN, "READY": CYAN, "CHANGES": YELLOW, "SKIPPED": GREY,
            "FAILED": RED, "BLOCKED": RED}
SEVERITIES = {"high": RED, "medium": YELLOW, "low": GREY}
MARKS = {"done": ("✓", CYAN), "current": ("●", f"bold {PINK}"), "next": ("○", GREY)}
CLIPBOARDS = (["clip"], ["pbcopy"], ["wl-copy"], ["xclip", "-selection", "clipboard"])
REF = re.compile(r"\[(\S+)( #\d+)?\]")
SHORTCUTS = 36  # questionary's limit for number and letter shortcuts

MENU = questionary.Style([
    ("qmark", f"fg:{PINK} bold"), ("question", "bold"), ("pointer", f"fg:{CYAN} bold"),
    ("highlighted", f"fg:{CYAN} bold"), ("answer", f"fg:{PINK} bold"), ("instruction", f"fg:{GREY}"),
    ("name", f"fg:{CYAN}"), ("ticket", f"fg:{PINK} bold"), ("does", f"fg:{GREY}"), ("fork", f"fg:{PINK}")])
GATE = questionary.Style([("qmark", f"fg:{YELLOW} bold"), ("question", "bold"), ("answer", f"fg:{YELLOW} bold")])


def log_line(line, colour=""):
    """A Log line (formats) with its ref, separators and outcome words in colour."""
    text = Text(line, style=colour)
    found = REF.match(line)
    if found:
        text.stylize(GREY, 0, found.end())
        text.stylize(CYAN, *found.span(1))
        if found.group(2):
            text.stylize(PINK, *found.span(2))
    text.highlight_regex(r" · ", GREY)
    for word, outcome in OUTCOMES.items():
        text.highlight_words([word], f"bold {outcome}")
    return text


def title(label):
    """A menu row from a choice label: the name, its `does` line, and a flow it switches to."""
    name, _, rest = label.partition(" ")
    if name.startswith("#"):
        return [("class:ticket", name), ("", f" {rest}")]
    does, arrow, flow = rest.partition(" → ")
    return [("class:name", name), ("class:does", f" {does}"), ("class:fork", f"{arrow}{flow}")]


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
        self.console = Console(highlight=False, soft_wrap=True)

    def say(self, line):
        self.console.print(log_line(line))

    def note(self, line):
        self.console.print(log_line(line, YELLOW))

    def outro(self, line):
        self.console.print(Text("└ ", style=CYAN) + log_line(line))

    def header(self, position, env, rail):
        line = Text.assemble((" dp ", f"bold #ffffff on {PINK}"), (" guide ", f"bold {CYAN}"), "  ")
        if not position:
            line.append("no position", GREY)
        else:
            line.append(f"{position['flow']} flow", CYAN)
            if position["ticket"]:
                line.append(" · ", GREY).append(f"#{position['ticket']}", f"bold {PINK}")
            line.append(" · ", GREY).append(position["step"], "bold").append(f"  {env} ", f"bold {YELLOW}")
        self.console.print()
        self.console.print(line)
        if rail:
            steps = [Text.assemble((MARKS[state][0], MARKS[state][1]), " ",
                                   (step, MARKS[state][1] if state == "current" else GREY)) for step, state in rail]
            self.console.print(Text(" ").append(Text(" ─ ", style=GREY).join(steps)))
        self.console.print()

    def job(self, prompt):
        copied = copy(prompt)
        self.console.print(Panel(Text(prompt, style="bold"), box=box.ROUNDED, border_style=PINK, expand=False,
                                 title="paste into a session", title_align="left",
                                 subtitle=Text("copied to the clipboard ✓", style=CYAN) if copied else None,
                                 subtitle_align="right"))

    def finding(self, finding):
        self.console.print(Text.assemble(
            (finding["id"], f"bold {PINK}"), " ", (finding["severity"], SEVERITIES.get(finding["severity"], GREY)),
            " ", (f"{finding['file']}:{finding['line']}", CYAN), " ", finding["finding"]))

    def busy(self, message):
        return self.console.status(Text(f"{message}…", style=GREY), spinner="dots", spinner_style=CYAN)

    def choose(self, message, options):
        index = questionary.select(
            message, [questionary.Choice(title(label), value=n) for n, (label, _) in enumerate(options)],
            qmark="◆", pointer="❯", style=MENU, use_shortcuts=len(options) <= SHORTCUTS,
            instruction="(arrows or a number)").unsafe_ask()
        return options[index][1]

    def confirm(self, message):
        return questionary.confirm(message, qmark="◆", style=GATE).unsafe_ask()

    def text(self, message, default):
        return questionary.text(message, default=default, qmark="◆", style=MENU).unsafe_ask()
