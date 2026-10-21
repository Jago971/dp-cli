"""dp guide: the flows at the terminal, with the agent called only for judgement.

Summary: finds the position, offers the next steps, and runs the chosen one:
         a person's gate (a pick, a human step, a tag, the review's
         dispositions) as a CLI prompt; an agent step as a job brief and the
         Job prompt to paste; a user-invoked skill as the command to type.
         Each step reached is written to .factory/guide.yaml, the guide
         skill's state file.
Input:   the repo root; prompts (a Plain: plain lines in tests and pipes, the
         coloured Terminal at a terminal); the Gitea connection (`offline`
         when it cannot be reached); git(*args).
Output:  the state file, job briefs, findings dispositions and log lines.
"""
import contextlib
import json
import re
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import yaml

from dp import brief, commands, flows
from dp.gitea import GiteaError

STATE = Path(".factory") / "guide.yaml"
BASE = "prep"
BRANCH_TYPES = {"TYPE/FEATURE": "feat", "TYPE/BUG": "fix", "TYPE/CHORE": "chore", "TYPE/DOCUMENTATION": "docs"}
SLUG_WORDS = 4
# The person's answers; the fix step turns them into the dispositions `formats` (Pull request) lists.
DISPOSITIONS = {"Fix": "fixed in the fix step", "Dismiss": "with a reason",
                "Escalate": "to someone", "Defer": "to a new Triage ticket"}


class Plain:
    """How the guide asks and shows, as plain lines through say(); Terminal adds colour.

    A subclass gives choose(message, [(label, value)]), confirm(message),
    text(message, default) and say(line).
    """

    def note(self, line):
        """A line the person should act on: a correction, Gitea unreachable."""
        self.say(line)

    def header(self, position, env, rail, does):
        """The position; a terminal adds the rail and the current step's `does` line."""
        self.say(header(position, env))

    def job(self, prompt):
        self.say(prompt)

    def outro(self, line):
        """The walk's last line."""
        self.say(line)

    def finding(self, finding):
        self.say(f"{finding['id']} · {finding['severity']} · {finding['file']}:{finding['line']} "
                 f"{finding['finding']}")

    def busy(self, message):
        """A context to wait in while Gitea answers."""
        return contextlib.nullcontext()


class Notes(Plain):
    """Collects the lines `dp guide --json` returns as `notes`."""

    def __init__(self):
        self.lines = []

    def say(self, line):
        self.lines.append(line)


def offline(error):
    """A Gitea connection that fails each call with the error that stopped it connecting."""
    def fail(*args):
        raise error
    return SimpleNamespace(call=fail, repo=None, human=fail)


def read_state(root):
    """The state file as {flow, step, ticket}, or None; a ticket that is not a number is dropped."""
    path = Path(root) / STATE
    state = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None
    if not isinstance(state, dict):
        return None
    ticket = state.get("ticket")
    return {"flow": state.get("flow"), "step": state.get("step"),
            "ticket": ticket if type(ticket) is int else None}


def write_state(root, position):
    """Write the position to the state file, in the guide skill's shape."""
    path = Path(root) / STATE
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"flow: {position['flow']}", f"step: {position['step']}"]
    lines += [f"ticket: {position['ticket']}"] if position["ticket"] else []
    lines += [f"updated: {datetime.now().isoformat(timespec='seconds')}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def ref(flow, ticket):
    """A log line's `[<flow> <ref>]` (formats, Log line)."""
    return f"[{flow} #{ticket}]" if ticket else f"[{flow}]"


def column_of(gitea, number):
    """The Board column ticket N sits in, or None when it is off the Board."""
    tickets = commands.column_tickets(gitea.call, gitea.repo)
    return next((title for title, listed in tickets.items() if any(t["number"] == number for t in listed)), None)


def locate(flow_map, state, gitea, prompts):
    """The position: the state file, corrected from the ticket's board column when Gitea answers."""
    column = None
    if state and state["flow"] == "ticket" and state["ticket"]:
        try:
            with prompts.busy("Reading the board"):
                column = column_of(gitea, state["ticket"])
        except GiteaError:
            prompts.note(f"{ref('ticket', state['ticket'])} Gitea unreachable · going on from {STATE.as_posix()}")
    position, corrected = flows.position(flow_map, state, column)
    if corrected:
        prompts.note(f"{ref('ticket', state['ticket'])} position · {state['step']} → {position['step']} "
                     "· from the board")
    return position


def show(root, gitea):
    """The position, its environment, any corrections and the choices, as `dp guide --json` prints them."""
    flow_map, notes = flows.load(), Notes()
    position = locate(flow_map, read_state(root), gitea, notes)
    return {"position": position, "env": position and flow_map["steps"][position["step"]]["env"],
            "notes": notes.lines, "choices": flows.choices(flow_map, position)}


def header(position, env):
    """The Guide prompt's first line (formats)."""
    if not position:
        return "Guide · no position"
    ticket = f" · #{position['ticket']}" if position["ticket"] else ""
    return f"Guide · {position['flow']} flow{ticket} · {position['step']} ({env})"


def label(choice, position):
    """A choice line (formats, Guide prompt): the name, its line, and a flow it switches to."""
    switches = position and choice["flow"] != position["flow"]
    return f"{choice['name']:<11} {choice['does']}" + (f" → {choice['flow']} flow" if switches else "")


def guide_prompt(shown):
    """The Guide prompt as text, for a session or a pipe."""
    labels = [label(choice, shown["position"]) for choice in shown["choices"]] + ["stop"]
    numbers = " / ".join(str(n) for n in range(1, len(labels) + 1))
    return "\n".join([*shown["notes"], header(shown["position"], shown["env"]),
                      *(f"{n}. {text}" for n, text in enumerate(labels, 1)), f"? Next? ({numbers})"])


def branch_name(ticket):
    """`<type>/<issue>-<slug>` (formats, Branch), the slug from the title before any colon."""
    kind = next((BRANCH_TYPES[name] for name in ticket["labels"] if name in BRANCH_TYPES), "feat")
    words = re.findall(r"[a-z0-9]+", ticket["title"].split(":")[0].lower())[:SLUG_WORDS]
    return f"{kind}/{ticket['number']}-{'-'.join(words)}"


def pick(prompts, gitea, git):
    """Take a Backlog ticket into In Progress, in a milestone, on its branch from prep; its number, or None."""
    try:
        with prompts.busy("Reading the Backlog"):
            backlog = commands.column_tickets(gitea.call, gitea.repo).get("Backlog", [])
    except GiteaError:
        prompts.note("[ticket] FAILED · Gitea unreachable · pick when it answers")
        return None
    if not backlog:
        prompts.note("[ticket] Backlog is empty · shape a ticket first")
        return None
    chosen = prompts.choose("Pick a ticket", [(f"#{t['number']} {t['title']}", t) for t in backlog]
                            + [("back", None)])
    if chosen is None:
        return None
    number = chosen["number"]
    with prompts.busy(f"Moving #{number}"):
        moved = commands.move(gitea.call, gitea.repo, number, "In Progress", assignee=gitea.human())
        joined = None if chosen["milestone"] else commands.join_earliest_milestone(gitea.call, gitea.repo, number)
    prompts.say(f"[ticket #{number}] {moved['from'] or 'off the Board'} → In Progress · assigned {moved['assigned']}")
    if joined:
        prompts.say(f"[ticket #{number}] joined {joined}")
    branch = prompts.text("Branch", branch_name(chosen))
    git("switch", "-c", branch, BASE)
    prompts.say(f"[ticket #{number}] branch {branch} from {BASE}")
    return number


def adjudicate(root, flow, ticket, prompts):
    """Ask the person for the disposition of each finding the review left undecided."""
    path = brief.folder(root, ticket, flow) / brief.FINDINGS
    if not path.is_file():
        return
    findings = json.loads(path.read_text(encoding="utf-8"))
    for finding in findings:
        if finding.get("disposition"):
            continue
        prompts.finding(finding)
        kind = prompts.choose(f"{finding['id']}?", [(f"{name:<9} {hint}", name) for name, hint in DISPOSITIONS.items()])
        if kind == "Dismiss":
            kind = f"Dismissed: {prompts.text('Reason', '')}"
        elif kind == "Escalate":
            kind = f"Escalated: {prompts.text('To whom', '')}"
        finding["disposition"] = kind
    path.write_text(json.dumps(findings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def job(flow_map, flow, step, ticket, gitea, git, prompts):
    """Gather a step's brief: the ticket in full and its column when Gitea answers, the diff stat, the skill."""
    details = column = None
    if ticket:
        try:
            with prompts.busy(f"Reading #{ticket}"):
                details, column = commands.issue(gitea.call, gitea.repo, ticket), column_of(gitea, ticket)
        except GiteaError:
            prompts.note(f"{ref(flow, ticket)} Gitea unreachable · the brief names the ticket only")
            details = {"number": ticket, "title": "", "body": "(Gitea was unreachable: read the ticket.)",
                       "comments": []}
    try:
        diffstat = git("diff", "--stat", "--merge-base", BASE)  # the branch's work, uncommitted included
    except GiteaError:
        diffstat = ""
    defined = flow_map["steps"][step]
    return brief.Job(flow=flow, step=step, does=defined["does"], env=defined["env"], ticket=details,
                     column=column, diffstat=diffstat, skills=brief.skill_text(defined))


def run(root, flow_map, position, choice, prompts, gitea, git):
    """Run the chosen step; the position it reached, or None when it did not happen."""
    flow, step = choice["flow"], choice["step"]
    ticket = position["ticket"] if position and flow == "ticket" else None
    skill = flow_map["steps"][step]["skill"]
    if step == "pick":
        ticket = pick(prompts, gitea, git)
        if ticket is None:
            return None
    elif skill == "human":
        if not prompts.confirm(f"{flow_map['steps'][step]['does']}. Done?"):
            return None
    elif brief.user_invoked(skill):
        prompts.say(f"Type /datumpin:{skill} in the session you worked in.")
    else:
        # A tag follows the release PR on main, whatever the state file says (guide skill).
        if step == "tag" and not prompts.confirm("Is the release PR merged on main?"):
            return None
        if step != "review":
            adjudicate(root, flow, ticket, prompts)
        work = job(flow_map, flow, step, ticket, gitea, git, prompts)
        path = brief.write(root, work)
        prompts.job(brief.prompt(work, path.relative_to(root)))
    reached = {"flow": flow, "step": step, "ticket": ticket}
    write_state(root, reached)
    return reached


def walk(root, prompts, gitea, git):
    """Offer the next steps and run each choice, until the person stops."""
    root, flow_map = Path(root), flows.load()
    position = locate(flow_map, read_state(root), gitea, prompts)
    while True:
        here = position and flow_map["steps"][position["step"]]
        prompts.header(position, here and here["env"], position and flows.rail(flow_map, position),
                       here and here["does"])
        offered = [(label(choice, position), choice) for choice in flows.choices(flow_map, position)]
        choice = prompts.choose("Next?", offered + [("stop", None)])
        if choice is None:
            break
        position = run(root, flow_map, position, choice, prompts, gitea, git) or position
    if position:
        write_state(root, position)
        prompts.outro(f"{ref(position['flow'], position['ticket'])} stopped · resume at {position['step']} · dp guide")
    else:
        prompts.outro("[guide] stopped")
