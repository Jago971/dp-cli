"""dp's command line: one command per repeated Gitea task, the guide and the token report.

Summary: `dp board`, `dp move`, `dp pick`, `dp pr`, `dp pointer`, `dp guide` and `dp tokens`.
Input:   the repo in the working directory (its git remote and
         `.claude/flow.yaml`) and tea's logins; writes go as the agent login.
Output:  compact text through Rich, which honours NO_COLOR, or JSON with
         `--json` for the agent; a Gitea failure prints one `dp:` line and
         exits 1.
"""
import functools
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import typer
from rich.console import Console

from dp import commands, guide, tokens
from dp.gitea import GiteaError, agent_login, human_username, logins, repo_slug, run, tea
from dp.terminal import Terminal

FULL_COLUMN = 8  # a longer column lists numbers only, as the formats Board view

app = typer.Typer(no_args_is_help=True, help="Repeated Gitea work and token reports for the datumpin flows.")
JSON = typer.Option(False, "--json", help="Print JSON for the agent.")


@dataclass
class Connection:
    call: Callable
    repo: str
    human: Callable[[], str]  # read only when a command needs it


def git(*args):
    result = run("git", *args)
    if result.returncode:
        raise GiteaError(f"git {args[0]}: {result.stderr.strip()}")
    return result.stdout.strip()


def repo_root():
    """The top of the git repo in the working directory."""
    return Path(git("rev-parse", "--show-toplevel"))


def connect():
    """The agent's Gitea call and the repo slug for the repo in the working directory."""
    agent = agent_login(repo_root())
    return Connection(call=tea(agent), repo=repo_slug(git("remote", "get-url", "origin")),
                      human=lambda: human_username(logins(), agent))


def current_branch():
    return git("branch", "--show-current")


def say(*lines, style=None):
    console = Console(soft_wrap=True)
    for line in lines:
        console.print(line, style=style, markup=False, highlight=False)


def emit(data, as_json, render):
    if as_json:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        render(data)


def reports_errors(command):
    """Turn a GiteaError into one `dp:` line and exit 1."""
    @functools.wraps(command)
    def wrapper(*args, **kwargs):
        try:
            return command(*args, **kwargs)
        except GiteaError as error:
            typer.echo(f"dp: {error}", err=True)
            raise typer.Exit(1)
    return wrapper


def ticket_line(ticket):
    return " · ".join([f"#{ticket['number']} {ticket['title']}", *ticket["labels"],
                       *([ticket["milestone"]] if ticket["milestone"] else [])])


def render_board(board):
    say(f"{board['repo']} · {len(board['pulls'])} PR", style="cyan")
    for column in board["columns"] + [{"title": "Unsorted", "tickets": board["unsorted"]}]:
        tickets = column["tickets"]
        say(f"{column['title'].upper()} ({len(tickets)})", style="cyan")
        if len(tickets) > FULL_COLUMN:
            say("  " + " ".join(f"#{t['number']}" for t in tickets))
        else:
            say(*(f"  {ticket_line(t)}" for t in tickets))
    say(*(f"Milestone  {m['title']} · {m['closed']} of {m['open'] + m['closed']} closed"
          for m in board["milestones"]))
    say(*(f"PR  #{p['number']} {p['title']} · {p['head']} → {p['base']}" for p in board["pulls"]))


@app.command()
@reports_errors
def board(as_json: bool = JSON):
    """The Board: every column and page, open issues off it, open PRs and milestones."""
    gitea = connect()
    emit(commands.board(gitea.call, gitea.repo), as_json, render_board)


@app.command()
@reports_errors
def move(number: int, column: str,
         assignee: str = typer.Option(None, help="Who In Progress assigns, when tea has several human logins."),
         as_json: bool = JSON):
    """Move ticket NUMBER to COLUMN; In Progress also assigns you."""
    gitea = connect()
    if column.lower() == "in progress":
        assignee = assignee or gitea.human()
    else:
        assignee = None
    moved = commands.move(gitea.call, gitea.repo, number, column, assignee=assignee)
    emit(moved, as_json, lambda m: say(
        f"#{m['number']} {m['from'] or 'off the Board'} → {m['to']}"
        + (f" · assigned {m['assigned']}" if m["assigned"] else "")))


@app.command()
@reports_errors
def pick(number: int,
         branch: str = typer.Option(None, help="The branch; by default <type>/<N>-<slug> from the ticket."),
         as_json: bool = JSON):
    """Take ticket NUMBER in: In Progress and assigned to you, in a milestone, on its branch from prep."""
    gitea = connect()
    ticket = commands.issue(gitea.call, gitea.repo, number)
    taken = guide.take(gitea, git, ticket, branch or guide.branch_name(ticket))
    emit(taken, as_json, lambda t: say(*guide.taken_lines(t)))


@app.command()
@reports_errors
def pr(title: str = typer.Option(..., help="The PR title, as a ticket title."),
       body_file: Path = typer.Option(..., exists=True, dir_okay=False, help="The PR body, in the formats shape."),
       labels: str = typer.Option("", help="Label names, comma-separated."),
       base: str = typer.Option("prep", help="The branch to merge into."),
       as_json: bool = JSON):
    """Open a PR from the current branch as the agent."""
    gitea = connect()
    names = [name.strip() for name in labels.split(",") if name.strip()]
    opened = commands.pr(gitea.call, gitea.repo, current_branch(), base, title,
                         body_file.read_text(encoding="utf-8"), names)
    emit(opened, as_json, lambda o: say(f"#{o['number']} {o['url']}"))


@app.command()
@reports_errors
def pointer(number: int, text: str, as_json: bool = JSON):
    """Post a Pointer comment on ticket NUMBER."""
    gitea = connect()
    posted = commands.pointer(gitea.call, gitea.repo, number, text)
    emit(posted, as_json, lambda p: say(f"#{p['number']} pointer posted"))


@app.command(name="guide")
@reports_errors
def guide_command(as_json: bool = JSON):
    """Walk the flows: the position, then the next steps as a menu; off a terminal, the Guide prompt."""
    root = repo_root()
    try:
        gitea = connect()
    except GiteaError as error:
        gitea = guide.offline(error)
    # Both ends: on Windows a null stdin (NUL) passes isatty().
    if as_json or not (sys.stdin.isatty() and sys.stdout.isatty()):
        emit(guide.show(root, gitea), as_json, lambda shown: say(guide.guide_prompt(shown)))
        return
    try:
        guide.walk(root, Terminal(), gitea, git)
    except KeyboardInterrupt:
        raise typer.Exit(130)


@app.command(name="tokens")
def tokens_command(log: Path = typer.Argument(..., exists=True, dir_okay=False, help="A session log (.jsonl)."),
                   as_json: bool = JSON):
    """Turns, tool calls and tokens per flow step of one session log."""
    with log.open(encoding="utf-8") as lines:
        rows = tokens.report(lines)
    emit(rows, as_json, lambda r: say(tokens.table(r)))


def main():
    """The `dp` command: UTF-8 out, whatever the console's code page, then the app."""
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    app()
