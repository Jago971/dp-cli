"""dp's command line: one command per repeated Gitea task, the guide and the token report.

Summary: `dp board`, `dp move`, `dp pick`, `dp pr`, `dp pointer`, `dp guide` and `dp tokens`.
Input:   the repo in the working directory (its git remote and
         `.claude/flow.yaml`) and tea's logins; writes go as the agent login.
Output:  text through dp.terminal (NO_COLOR, `--plain` and pipes give it
         unstyled), or JSON with `--json` for the agent; a Gitea failure
         prints one `✖ dp:` line and exits 1.
"""
import functools
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import typer

from dp import commands, guide, tokens
from dp.gitea import GiteaError, agent_login, human_username, logins, repo_slug, run, tea
from dp.terminal import Terminal, at_terminal, busy, done, failed, say, show_board, use_plain

app = typer.Typer(no_args_is_help=True, help="Repeated Gitea work and token reports for the datumpin flows.")
JSON = typer.Option(False, "--json", help="Print JSON for the agent.")


@app.callback()
def options(plain: bool = typer.Option(False, "--plain", help="No colour and no spinners, for logs.")):
    use_plain(plain)


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


def emit(data, as_json, render):
    if as_json:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        render(data)


def reports_errors(command):
    """Turn a GiteaError into one `✖ dp:` line and exit 1."""
    @functools.wraps(command)
    def wrapper(*args, **kwargs):
        try:
            return command(*args, **kwargs)
        except GiteaError as error:
            failed(f"dp: {error}")
            raise typer.Exit(1)
    return wrapper


@app.command()
@reports_errors
def board(as_json: bool = JSON):
    """The Board: every column and page, open issues off it, open PRs and milestones."""
    gitea = connect()
    with busy("Reading the board", quiet=as_json):
        listing = commands.board(gitea.call, gitea.repo)
    emit(listing, as_json, show_board)


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
    with busy(f"Moving #{number}", quiet=as_json):
        moved = commands.move(gitea.call, gitea.repo, number, column, assignee=assignee)
    emit(moved, as_json, lambda m: done(
        f"#{m['number']} {m['from'] or 'off the Board'} → {m['to']}"
        + (f" · assigned {m['assigned']}" if m["assigned"] else "")))


@app.command()
@reports_errors
def pick(number: int = typer.Argument(None, help="The ticket; at a terminal, without it, a Backlog menu."),
         branch: str = typer.Option(None, help="The branch; by default <type>/<N>-<slug> from the ticket."),
         as_json: bool = JSON):
    """Take ticket NUMBER in: In Progress and assigned to you, in a milestone, on its branch from prep."""
    gitea = connect()
    if number is None:
        if as_json or not at_terminal():
            raise GiteaError("give a ticket number off a terminal: dp pick N")
        guide.pick(Terminal(), gitea, git)
        return
    with busy(f"Taking #{number} in", quiet=as_json):
        ticket = commands.issue(gitea.call, gitea.repo, number)
        taken = guide.take(gitea, git, ticket, branch or guide.branch_name(ticket))
    emit(taken, as_json, lambda t: (say(*guide.taken_lines(t)[:-1]), done(guide.taken_lines(t)[-1])))


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
    with busy("Opening the PR", quiet=as_json):
        opened = commands.pr(gitea.call, gitea.repo, current_branch(), base, title,
                             body_file.read_text(encoding="utf-8"), names)
    emit(opened, as_json, lambda o: done(f"#{o['number']} {o['url']}"))


@app.command()
@reports_errors
def pointer(number: int, text: str, as_json: bool = JSON):
    """Post a Pointer comment on ticket NUMBER."""
    gitea = connect()
    with busy(f"Posting on #{number}", quiet=as_json):
        posted = commands.pointer(gitea.call, gitea.repo, number, text)
    emit(posted, as_json, lambda p: done(f"#{p['number']} pointer posted"))


@app.command(name="guide")
@reports_errors
def guide_command(as_json: bool = JSON):
    """Walk the flows: the position, then the next steps as a menu; off a terminal, the Guide prompt."""
    root = repo_root()
    try:
        gitea = connect()
    except GiteaError as error:
        gitea = guide.offline(error)
    if as_json or not at_terminal():
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
