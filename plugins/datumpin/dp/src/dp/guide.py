"""dp guide: the flows at the terminal, with the agent called only for judgement.

Summary: finds the position, offers the next steps (this flow's first, then
         the forks that hold, `flows…` and stop), and runs the chosen one: a
         person's gate (a pick, a human step, the review's
         dispositions, leaving `test`) as a CLI prompt; `gate` and `tag` as dp's own
         commands, no agent turn; an agent step as a
         job brief and a Claude session on the step's model, or the Job
         prompt to paste; a user-invoked skill as the command to type. Each
         step reached is written to .factory/guide.yaml, the guide skill's
         state file, with the ticket flows it holds paused (the home menu
         resumes one; `pause` saves one and returns there).
Input:   the repo root; prompts (a Plain: plain lines in tests and pipes, the
         coloured Terminal at a terminal); the Gitea connection (`offline`
         when it cannot be reached); git(*args).
Output:  the state file, job briefs, findings dispositions, Tested Pointers
         and log lines.
"""
import contextlib
import json
import os
import re
from urllib.parse import quote
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import yaml

from dp import brief, commands, flows
from dp.gitea import GiteaError

STATE = Path(".factory") / "guide.yaml"
BASE = "prep"
START = f"origin/{BASE}"  # a branch starts from the remote, so it is current whatever local prep holds
PROMOTION = "origin/main...prep"  # what a release promotes; the release flow runs on prep, so BASE is empty there
BRANCH_TYPES = {"TYPE/FEATURE": "feat", "TYPE/BUG": "fix", "TYPE/CHORE": "chore", "TYPE/DOCUMENTATION": "docs"}
SLUG_WORDS = 4
# The person's answers, each with its effect; what the person chooses is recorded in the wording `formats`
# (Pull request) lists, not in these menu words.
DISPOSITIONS = {"Fix": "goes to the fix step", "Dismiss": "asks a reason, records it",
                "Escalate": "asks to whom, records it", "Defer": "opens a new Triage ticket"}
NEXT_STEP = "Next: choose the next step in dp guide"  # the closing line of a step the person finishes
LEAVING_TEST = 'Test it by hand where it runs; leaving this step asks "Tested OK?" and records it'
TESTED_DEFECT = "Defect at test"
TESTED = "Tested by hand"  # the Event of the Pointer leaving `test` posts; milestone_tested looks for it
BEFORE_TESTING = ("Triage", "Backlog", "In Progress", "Review")
SEPARATOR_VALUE = "separator"
SEPARATOR = ("─" * 11, SEPARATOR_VALUE)
STOP = f"{'stop':<11} saves the position and exits"
BACK = f"{'back':<11} returns to the guide"
FLOWS = (f"{'flows…':<11} Start or switch to any flow", "flows")
PAUSE = (f"{'pause':<11} Saves this ticket's step, returns to the home menu", "pause")
RESUME = (f"{'resume…':<11} Continue a paused ticket", "resume")
HOME_FLOWS = ("ticket", "session")  # reached by `tickets` and `end`, so `flows…` leaves them out
NEW_CHAT = "Next session: run dp guide in dp-cli and choose the ticket and step the handoff recommends."
END = {"name": "end", "step": "retro", "flow": "session", "kind": "flow",
       "does": "Review the session, then write the handoff"}


class Plain:
    """How the guide asks and shows, as plain lines through say(); Terminal adds colour.

    A subclass gives choose(message, [(label, value)], default=None) (the
    default is a value to preselect), confirm(message), text(message,
    default) and say(line).
    """

    def note(self, line):
        """A line the person should act on: a correction, Gitea unreachable."""
        self.say(line)

    def header(self, position, env, rail, does):
        """The position; a terminal adds the rail and the current step's `does` line."""
        self.say(header(position, env))

    def job(self, prompt, model, effort):
        """Hand an agent step to Claude: here, the Job prompt to paste; a terminal starts a session."""
        self.say(prompt)
        self.say("Next: paste it into a session, then /exit and run dp guide")

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


def as_int(value):
    return value if type(value) is int else None


def read_state(root):
    """The state file as {flow, step, ticket, paused}, or None; a ticket that is not a number is dropped.

    `paused` lists the ticket flow positions the guide holds, each as {flow, step, ticket}.
    """
    path = Path(root) / STATE
    state = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None
    if not isinstance(state, dict):
        return None
    held = state.get("paused") if isinstance(state.get("paused"), list) else []
    paused = [{"flow": "ticket", "step": entry.get("step"), "ticket": as_int(entry.get("ticket"))}
              for entry in held if isinstance(entry, dict) and as_int(entry.get("ticket"))]
    return {"flow": state.get("flow"), "step": state.get("step"), "ticket": as_int(state.get("ticket")),
            "paused": paused}


def write_state(root, position, paused=()):
    """Write the position (None at the home menu) and the paused tickets to the state file in the guide skill's shape."""
    path = Path(root) / STATE
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"flow: {position['flow']}", f"step: {position['step']}"] if position else []
    lines += [f"ticket: {position['ticket']}"] if position and position["ticket"] else []
    lines += ["paused:", *(f"  - {{ticket: {p['ticket']}, step: {p['step']}}}" for p in paused)] if paused else []
    lines += [f"updated: {datetime.now().isoformat(timespec='seconds')}"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def ref(flow, ticket):
    """A log line's `[<flow> <ref>]` (formats, Log line)."""
    return f"[{flow} #{ticket}]" if ticket else f"[{flow}]"


def column_of(gitea, ticket):
    """The Board column ticket N sits in, or None when it is off the Board."""
    tickets = commands.column_tickets(gitea.call, gitea.repo)
    return next((title for title, listed in tickets.items() if any(t["number"] == ticket for t in listed)), None)


def locate(flow_map, state, gitea, prompts):
    """(position, pending): the state file, corrected from the ticket's board column when Gitea answers.

    `pending` when the board placed the ticket at a step that has not run, so the menu offers it."""
    column = None
    if state and state["flow"] == "ticket" and state["ticket"]:
        try:
            with prompts.busy("Reading the board"):
                column = column_of(gitea, state["ticket"])
        except GiteaError:
            prompts.note(f"{ref('ticket', state['ticket'])} Gitea unreachable · going on from {STATE.as_posix()}")
    position, corrected = flows.position(flow_map, state and {k: state[k] for k in ("flow", "step", "ticket")},
                                         column)
    if corrected:
        prompts.note(f"{ref('ticket', state['ticket'])} position · {state['step']} → {position['step']} "
                     "· from the board")
    return position, corrected


def unscoped(gitea, ticket, root):
    """True when the ticket has no Acceptance section (formats, Ticket)."""
    return bool(ticket) and "## Acceptance" not in commands.issue(gitea.call, gitea.repo, ticket)["body"]


def tested(gitea, ticket, root=None):
    """True when the ticket's latest test verdict is a Tested Pointer, so a defect since then means a retest."""
    verdicts = [c["text"] for c in commands.issue(gitea.call, gitea.repo, ticket)["comments"]
                if c["text"].startswith((f"{TESTED}, ", f"{TESTED_DEFECT}, "))]
    return bool(verdicts) and verdicts[-1].startswith(f"{TESTED}, ")


def milestone_tested(gitea, ticket, root):
    """True when every other open ticket in the ticket's milestone is past Testing, or in Testing or DoD with a Tested Pointer."""
    milestone = ticket and commands.issue(gitea.call, gitea.repo, ticket)["milestone"]
    if not milestone:
        return False
    placed = commands.column_tickets(gitea.call, gitea.repo)
    others = {column: [t["number"] for t in placed.get(column, [])
                       if t["milestone"] == milestone and t["number"] != ticket]
              for column in (*BEFORE_TESTING, "Testing", "DoD")}
    if any(others[column] for column in BEFORE_TESTING):
        return False
    return all(commands.each(lambda n: tested(gitea, n), others["Testing"] + others["DoD"]))


VERSION = re.compile(r"v\d+\.\d+\.\d+")


def release_version(title):
    """The leading vX.Y.Z of a milestone or release PR title (`vX.Y.Z – <theme>`), else the title as is."""
    found = re.match(VERSION, title)
    return found.group() if found else title


def gate(gitea, milestone):
    """Move each open ticket of the milestone to DoD; the numbers moved.

    Process: a ticket without a Tested Pointer stops the gate before any move, so a release is never half gated.
    """
    open_tickets = [t["number"] for column in commands.column_tickets(gitea.call, gitea.repo).values()
                    for t in column if t["milestone"] == milestone]
    untested = [n for n, ok in zip(open_tickets, commands.each(lambda n: tested(gitea, n), open_tickets)) if not ok]
    if untested:
        raise GiteaError(f"no Tested Pointer: {', '.join(f'#{n}' for n in untested)}")
    for number in open_tickets:
        commands.move(gitea.call, gitea.repo, number, "DoD")
    return open_tickets


def tag(gitea, git, prompts, version):
    """Tag main's tip `version` and push the tag after a confirm; False when declined.

    Process: the version must be vX.Y.Z and its release PR (titled `vX.Y.Z – <theme>`, formats) must be merged on
    main, else GiteaError, so a tag never lands before the release does.
    """
    if not VERSION.fullmatch(version):
        raise GiteaError(f"{version!r} is not a vX.Y.Z version")
    pulls = [p for p in commands.paged(gitea.call, f"repos/{gitea.repo}/pulls?state=all")
             if p["base"]["ref"] == "main" and release_version(p["title"]) == version]
    latest = max(pulls, key=lambda p: p["number"], default=None)
    if not latest or not latest["merged"]:
        which = f"#{latest['number']}" if latest else f"for {version}"
        raise GiteaError(f"release PR {which} is not merged on main")
    if not prompts.confirm(f"Tag {version} on main and push it?"):
        return False
    git("fetch", "origin", "main")
    git("tag", version, "origin/main")
    git("push", "origin", version)
    return True


def deploys_images(gitea, ticket, root):
    """True when the repo has a Dockerfile, so it builds images a server can pull."""
    for _, subfolders, files in os.walk(root):
        subfolders[:] = [s for s in subfolders if not s.startswith(".") and s not in ("node_modules", "build", "dist")]
        if any(name.startswith("Dockerfile") for name in files):
            return True
    return False


CHECKS = {"unscoped": unscoped, "milestone_tested": milestone_tested, "deploys_images": deploys_images}


def checks(root, gitea, position, prompts):
    """holds(check) for a fork's `when` at this position; a check Gitea cannot answer holds, so the person decides."""
    def holds(check):
        try:
            with prompts.busy("Checking"):
                return CHECKS[check](gitea, position and position["ticket"], root)
        except GiteaError:
            return True
    return holds


def show(root, gitea):
    """The position, its environment, any corrections and the choices, as `dp guide --json` prints them."""
    flow_map, notes = flows.load(), Notes()
    state = read_state(root)
    position, pending = locate(flow_map, state, gitea, notes)
    return {"position": position, "env": position and flow_map["steps"][position["step"]]["env"],
            "paused": state and state["paused"], "notes": notes.lines,
            "choices": flows.choices(flow_map, position, checks(root, gitea, position, notes), pending)}


def header(position, env):
    """The Guide prompt's first line (formats)."""
    if not position:
        return "Guide · start"
    ticket = f" · #{position['ticket']}" if position["ticket"] else ""
    return f"Guide · {position['flow']} flow{ticket} · {position['step']} ({env})"


def label(choice, position, pull=None):
    """A choice line (formats, Guide prompt): the name, its line, and a flow it switches to.

    `merge` names the ticket's PR when `pull` found one."""
    switches = position and choice["flow"] != position["flow"]
    does = choice["does"].replace("the PR", f"PR #{pull[0]}") if pull and choice["name"] == "merge" else choice["does"]
    return f"{choice['name']:<11} {does}" + (f" → {choice['flow']} flow" if switches else "")


def home(offered, paused):
    """The menu with no ticket current: tickets, resume (when one is paused), end session, flows."""
    tickets = next(c for c in offered if c["name"] == "ticket")
    return [(f"{'tickets':<11} Pick a Backlog ticket", tickets), *([RESUME] if paused else []),
            (label(END, None), END), FLOWS]


def menu(offered, position, pull=None, paused=()):
    """The options: this flow's steps, a separator, the forks, `flows…` and, in a ticket, `pause`; then stop.

    At the end of a flow, or with no position, the home menu.
    """
    if offered[0]["kind"] == "flow":
        return home(offered, paused) + [(STOP, None)]
    options = [(label(c, position, pull), c) for c in offered if c["kind"] != "fork"]
    options += [SEPARATOR, *((label(c, position), c) for c in offered if c["kind"] == "fork"), FLOWS]
    return options + ([PAUSE] if position["flow"] == "ticket" and position["ticket"] else []) + [(STOP, None)]


def guide_prompt(shown):
    """The Guide prompt as text, for a session or a pipe."""
    lines, count = [*shown["notes"], header(shown["position"], shown["env"])], 0
    for text, value in menu(shown["choices"], shown["position"], paused=shown["paused"]):
        if value == SEPARATOR_VALUE:
            lines.append(f"   {text}")
        else:
            count += 1
            lines.append(f"{count}. {text}")
    return "\n".join(lines + [f"? Next? ({' / '.join(str(n) for n in range(1, count + 1))})"])


def branch_name(ticket):
    """`<type>/<issue>-<slug>` (formats, Branch), the slug from the title before any colon."""
    kind = next((BRANCH_TYPES[name] for name in ticket["labels"] if name in BRANCH_TYPES), "feat")
    words = re.findall(r"[a-z0-9]+", ticket["title"].split(":")[0].lower())[:SLUG_WORDS]
    return f"{kind}/{ticket['number']}-{'-'.join(words)}"


def has_branch(git, branch, merged=False):
    """True when git lists the branch; with `merged`, only when prep contains it."""
    return bool(git("branch", *(("--merged", BASE) if merged else ()), "--list", branch).strip())


def settle_branch(prompts, git, branch):
    """(branch, create): the name to work on once an existing branch of that name is dealt with.

    Output: `create` False when the person switches to the old branch."""
    while has_branch(git, branch):
        options = [("Switch    to the existing branch", "switch")]
        # git refuses to delete the checked-out branch
        if has_branch(git, branch, merged=True) and git("branch", "--show-current").strip() != branch:
            options.append(("Delete    it, merged into prep, and start a new one", "delete"))
        options.append(("Name      a new branch", "name"))
        answer = prompts.choose(f"Branch {branch} exists", options)
        if answer == "switch":
            return branch, False
        if answer == "delete":
            git("branch", "-d", branch)
        else:
            branch = prompts.text("Branch", branch)
    return branch, True


def take(gitea, git, ticket, branch, create=True):
    """Move the ticket to In Progress (assigning the person), into the open milestone due first when it has
    none, and branch from origin/prep, fetched first so it is current; what happened, as `dp pick --json`
    prints it. A failed fetch raises before anything moves."""
    try:
        git("fetch", "origin")
        moved = commands.move(gitea.call, gitea.repo, ticket["number"], "In Progress", assignee=gitea.human())
        joined = None if ticket["milestone"] else commands.join_earliest_milestone(gitea.call, gitea.repo, ticket["number"])
    except GiteaError as error:
        raise GiteaError(f"{error} · ticket not moved, pick when it answers") from error
    # one argument, so a leading-dash branch is not an option
    try:
        if create:
            git("switch", f"--create={branch}", START)
        else:
            git("switch", branch)
    except GiteaError as error:
        raise GiteaError(f"{error} · ticket #{ticket['number']} is In Progress, switch the branch by hand") from error
    return {**moved, "milestone": joined or ticket["milestone"], "joined": bool(joined), "branch": branch}


def taken_lines(taken):
    at = f"[ticket #{taken['number']}]"
    return [f"{at} {taken['from'] or 'off the Board'} → In Progress · assigned {taken['assigned']}",
            *([f"{at} joined {taken['milestone']}"] if taken["joined"] else []),
            f"{at} branch {taken['branch']} from {START}"]


def pick(prompts, gitea, git):
    """Take a Backlog ticket in (take); its number, or None."""
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
                            + [(BACK, None)])
    if chosen is None:
        return None
    branch, create = settle_branch(prompts, git, prompts.text("Branch", branch_name(chosen)))
    try:
        with prompts.busy(f"Moving #{chosen['number']}"):
            taken = take(gitea, git, chosen, branch, create)
    except GiteaError as error:
        prompts.note(f"dp: {error}")
        return None
    for line in taken_lines(taken):
        prompts.say(line)
    prompts.say(NEXT_STEP)
    return chosen["number"]


def covering(gitea, ticket, finding):
    """Numbers of the other open tickets whose title names the finding's file; none when Gitea cannot say."""
    try:
        found = commands.paged(gitea.call, f"repos/{gitea.repo}/issues?state=open&type=issues&q={quote(finding['file'])}")
    except GiteaError:
        return []
    return [i["number"] for i in found if i["number"] != ticket and finding["file"] in i["title"]]


def adjudicate(root, flow, ticket, prompts, gitea=None):
    """Ask the person for the disposition of each finding the review left undecided.

    Output: the step the dispositions point to (`fix` when one is to fix or
    defer, else `pr`), or None without findings.
    """
    path = brief.folder(root, ticket, flow) / brief.FINDINGS
    if not path.is_file():
        return None
    findings = json.loads(path.read_text(encoding="utf-8"))
    for finding in findings:
        if finding.get("disposition"):
            continue
        prompts.finding(finding)
        covered = covering(gitea, ticket, finding) if gitea else []
        hints = {**DISPOSITIONS, "Defer": DISPOSITIONS["Defer"] + "; open " + ", ".join(f"#{n}" for n in covered) + " may cover it"} if covered else DISPOSITIONS
        kind = prompts.choose(f"{finding['id']}?", [(f"{name:<9} {hint}", name) for name, hint in hints.items()])
        if kind == "Dismiss":
            kind = f"Dismissed: {prompts.text('Reason', '')}"
        elif kind == "Escalate":
            kind = f"Escalated: {prompts.text('To whom', '')}"
        finding["disposition"] = kind
    path.write_text(json.dumps(findings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return "fix" if any(f.get("disposition") in ("Fix", "Defer") for f in findings) else "pr"


def recorded(root, flow, ticket, prompts):
    """Say the dispositions already recorded for the flow's findings, one line each."""
    path = brief.folder(root, ticket, flow) / brief.FINDINGS
    if path.is_file():
        for finding in json.loads(path.read_text(encoding="utf-8")):
            if finding.get("disposition"):
                prompts.say(f"{ref(flow, ticket)} {finding['id']} {finding['disposition']}")


def leave_test(position, prompts, gitea, env, answered=False):
    """Leaving `test` records the hand test as a Pointer on the ticket; False to stay at `test`.

    Input: `answered` when the person chose `finish`, which is the answer to "Tested OK?".
    """
    ticket = position["ticket"]
    try:
        if tested(gitea, ticket):  # a cancelled pick left us at `test` after the Pointer posted
            return True
    except GiteaError:
        prompts.note(f"[ticket #{ticket}] Gitea unreachable · cannot check for a Pointer · asking")
    if not answered and not prompts.confirm("Tested OK?"):
        prompts.note(f"[ticket #{ticket}] not tested · staying at test")
        return False
    where = prompts.text("Where, and what you checked", env).strip().rstrip(".") or env
    text = f"{TESTED}, {datetime.now():%Y-%m-%d}. Done: {where}. → #{ticket}"
    try:
        with prompts.busy("Posting"):
            commands.pointer(gitea.call, gitea.repo, ticket, text)
        prompts.say(f"[ticket #{ticket}] tested · Pointer posted")
    except GiteaError:
        prompts.note(f"[ticket #{ticket}] FAILED · Gitea unreachable · post it later: {text}")
    return True


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
    if flow == "release":
        diffstat = git("diff", "--stat", PROMOTION)  # a git error stops the step, it is not an empty diff
    else:
        try:
            diffstat = git("diff", "--stat", "--merge-base", BASE)  # the branch's work, uncommitted included
        except GiteaError:
            diffstat = ""
    defined = flow_map["steps"][step]
    return brief.Job(flow=flow, step=step, does=defined["does"], env=defined["env"], ticket=details,
                     column=column, diffstat=diffstat, skills=brief.skill_text(defined))


def merge_state(gitea, git, ticket):
    """The ticket's PR as (number, "merged" | "open" | "closed", url), or None when it has none or Gitea cannot say.

    The newest PR whose body has `Refs #N`; else the current branch's PR. Gitea reads a merged PR's head as
    `refs/pull/N/head`, so the head name alone cannot find it."""
    try:
        pulls = commands.paged(gitea.call, f"repos/{gitea.repo}/pulls?state=all")
    except GiteaError:
        return None
    refs = re.compile(rf"\bRefs\b[^\n]*#{ticket}\b")  # the Refs line can list several tickets
    pull = max((p for p in pulls if refs.search(p.get("body") or "")), key=lambda p: p["number"], default=None)
    if not pull:
        try:
            branch = git("branch", "--show-current").strip()
        except GiteaError:  # a failing git falls back to asking
            return None
        pull = next((p for p in pulls if p["head"]["ref"] == branch), None)
    if not pull:
        return None
    state = "merged" if pull["merged"] else pull.get("state", "open")
    return pull["number"], state, pull.get("html_url", "")


def confirm_done(step, does, ticket, prompts, pull):
    """True when a person's step is done: `merge` reads the PR's state (`pull`), any other step asks."""
    if pull and pull[1] == "merged":
        return True
    if pull and pull[1] == "closed":
        prompts.note(f"{ref('ticket', ticket)} PR #{pull[0]} is closed, not merged · reopen it or open a new one, then run dp guide")
        return False
    if pull:
        prompts.note(f"{ref('ticket', ticket)} PR #{pull[0]} is not merged · merge it, then run dp guide")
        return False
    return prompts.confirm(f"{does}. Done?")


def release_step(step, prompts, gitea, git):
    """Run `gate` or `tag` as dp does, asking the milestone (the open one due first by default); False to stay."""
    found = commands.earliest_milestone(gitea.call, gitea.repo)
    milestone = prompts.text("Milestone", found["title"] if found else "").strip()
    if not milestone:
        raise GiteaError("no open milestone: give one")
    if step == "gate":
        moved = gate(gitea, milestone)
        prompts.say(f"[release] gate · {len(moved)} to DoD · {milestone}")
        return True
    return tag(gitea, git, prompts, release_version(milestone))


def run(root, flow_map, position, choice, prompts, gitea, git, pull=None):
    """Run the chosen step; the position it reached, or None when it did not happen.

    `pull` is the ticket's PR as `merge_state` found it for the menu; `merge` reads it again after the choice."""
    flow, step = choice["flow"], choice["step"]
    ticket = position["ticket"] if position and flow == "ticket" else None
    skill = flow_map["steps"][step]["skill"]
    if step == "pick":
        ticket = pick(prompts, gitea, git)
        if ticket is None:
            return None
    elif step == "finish":
        try:
            column = commands.finish(gitea.call, gitea.repo, ticket)  # the Pointer was posted on leaving `test`
        except GiteaError:
            prompts.note(f"{ref(flow, ticket)} FAILED · Gitea unreachable · staying at test")
            return None
        prompts.say(f"{ref(flow, ticket)} DONE · closed, in {column or 'no column'}")
    elif step == "defect":
        found = prompts.text("What failed", "").strip().rstrip(".") or "a defect at test"
        text = f"{TESTED_DEFECT}, {datetime.now():%Y-%m-%d}. Landed: merged to prep. Left: {found}. → Backlog"
        try:
            commands.reopen(gitea.call, gitea.repo, ticket, text)
        except GiteaError:
            prompts.note(f"{ref(flow, ticket)} FAILED · Gitea unreachable · staying at test")
            return None
        prompts.say(f"{ref(flow, ticket)} reopened · Backlog · {found}")
    elif skill == "dp":
        reached = release_step(step, prompts, gitea, git)
        if not reached:
            return None
    elif skill == "human":
        does = flow_map["steps"][step]["does"]
        if step == "test":
            prompts.say(LEAVING_TEST)  # leaving `test` asks "Tested OK?", so entering it does not ask "Done?"
        elif step == "sign-off":
            recorded(root, flow, ticket, prompts)  # what the person signs; nothing is asked again
        if step == "merge" and pull:
            prompts.say(f"PR #{pull[0]} {pull[2]}".strip())
        if step == "merge":
            pull = merge_state(gitea, git, ticket) or pull  # the person may have merged since the menu drew; a failed read keeps the menu's
        if step != "test" and not confirm_done(step, does, ticket, prompts, pull if step == "merge" else None):
            return None
        prompts.say(NEXT_STEP)
    elif brief.user_invoked(skill):
        prompts.say(f"Type /datumpin:{skill} in the session you worked in.")
        prompts.say(NEW_CHAT if step == "handoff" else "Next: type it there, then run dp guide")
    else:
        if step != "review":
            adjudicate(root, flow, ticket, prompts, gitea)  # findings a resumed walk passed by undecided
        work = job(flow_map, flow, step, ticket, gitea, git, prompts)
        if flow == "release" and step == "review" and not work.diffstat.strip():
            raise GiteaError(f"empty diff {PROMOTION}: nothing to review, no findings written")
        path = brief.write(root, work)
        model = brief.skill_header(skill)
        prompts.say(f"{ref(flow, ticket)} Claude · {work.does} · /exit returns to the guide")
        prompts.job(brief.prompt(work, path.relative_to(root)), model.get("model"), model.get("effort"))
    return {"flow": flow, "step": step, "ticket": ticket}


def choose_flow(flow_map, prompts):
    started = [c for c in flows.flow_starts(flow_map) if c["flow"] not in HOME_FLOWS]  # ticket and session have entries
    return prompts.choose("Flow?", [(label(c, None), c) for c in started] + [(BACK, None)])


def choose_paused(paused, prompts):
    """The paused ticket the person resumes, or None for back."""
    return prompts.choose("Resume?", [(f"#{p['ticket']} at {p['step']}", p) for p in paused] + [(BACK, None)])


def may_leave(position, here, choice, prompts, gitea, pending=False):
    """Leaving a step: `test` needs its Tested Pointer first, unless a defect reopens it; False to stay.

    Input: `pending` when the board placed the ticket at `test`, so choosing `test` enters it."""
    if pending and choice["step"] == "test":
        return True
    if position and position["step"] == "test" and position["ticket"] and choice["step"] != "defect":
        return leave_test(position, prompts, gitea, here["env"], answered=choice["step"] == "finish")
    return True


def hold(paused, position):
    """The paused tickets with this ticket flow position added, replacing the same ticket's step."""
    return [p for p in paused if p["ticket"] != position["ticket"]] + [position]


def still_paused(position, reached, paused):
    """The paused tickets after a step: the ticket left is held, a ticket worked again is not."""
    if position and position["flow"] == "ticket" and position["ticket"] \
            and (reached["flow"] != "ticket" or reached["ticket"] != position["ticket"]):
        paused = hold(paused, position)
    return [p for p in paused if p["ticket"] != reached["ticket"]]


def walk(root, prompts, gitea, git):
    """Offer the next steps and run each choice, until the person stops."""
    root, flow_map = Path(root), flows.load()
    state = read_state(root)
    paused = state["paused"] if state else []
    position, pending = locate(flow_map, state, gitea, prompts)
    while True:
        # A review's dispositions come before the menu, so they can preselect fix or pr.
        preselect = position and position["step"] == "review" \
            and adjudicate(root, position["flow"], position["ticket"], prompts, gitea)
        here = position and flow_map["steps"][position["step"]]
        prompts.header(position, here and here["env"], position and flows.rail(flow_map, position),
                       here and here["does"])
        offered = flows.choices(flow_map, position, checks(root, gitea, position, prompts), pending)
        at_merge = position and position["ticket"] and any(c["step"] == "merge" for c in offered)
        pull = merge_state(gitea, git, position["ticket"]) if at_merge else None
        options = menu(offered, position, pull, paused)
        default = next((v for _, v in options if isinstance(v, dict) and v["step"] == preselect), None)
        choice = prompts.choose("Next?", options, default)
        if choice is None:
            break
        if choice == "pause":
            paused, pending = hold(paused, position), False
            prompts.say(f"{ref('ticket', position['ticket'])} paused · {position['step']} · home menu")
            position = None
            write_state(root, position, paused)
            continue
        if choice == "resume":
            entry = choose_paused(paused, prompts)
            if entry:
                (position, pending), paused = locate(flow_map, entry, gitea, prompts), still_paused(None, entry, paused)
                write_state(root, position, paused)
            continue
        if choice == "flows":
            choice = choose_flow(flow_map, prompts)
            if not isinstance(choice, dict):
                continue
        if not may_leave(position, here, choice, prompts, gitea, pending):
            continue
        reached = run(root, flow_map, position, choice, prompts, gitea, git, pull)
        if reached:
            paused = still_paused(position, reached, paused)
            position, pending = (None if reached["step"] == "finish" else reached), False  # a finished ticket lands home
            write_state(root, position, paused)
    write_state(root, position, paused)
    if position:
        prompts.outro(f"{ref(position['flow'], position['ticket'])} stopped · resume at {position['step']} · dp guide")
    else:
        prompts.outro("[guide] stopped")
