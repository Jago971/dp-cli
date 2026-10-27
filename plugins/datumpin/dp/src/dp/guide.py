"""dp guide: the flows at the terminal, with the agent called only for judgement.

Summary: finds the position, offers the next steps (this flow's first, then
         the forks that hold, `flows…` and stop), and runs the chosen one: a
         person's gate (a pick, a human step, a tag, the review's
         dispositions, leaving `test`) as a CLI prompt; an agent step as a
         job brief and a Claude session on the step's model, or the Job
         prompt to paste; a user-invoked skill as the command to type. Each
         step reached is written to .factory/guide.yaml, the guide skill's
         state file, with the ticket flow it paused when it left one.
Input:   the repo root; prompts (a Plain: plain lines in tests and pipes, the
         coloured Terminal at a terminal); the Gitea connection (`offline`
         when it cannot be reached); git(*args).
Output:  the state file, job briefs, findings dispositions, Tested Pointers
         and log lines.
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

    `paused` is the ticket flow's position when the guide left it, or None.
    """
    path = Path(root) / STATE
    state = yaml.safe_load(path.read_text(encoding="utf-8")) if path.is_file() else None
    if not isinstance(state, dict):
        return None
    paused = as_int(state.get("paused_ticket"))
    return {"flow": state.get("flow"), "step": state.get("step"), "ticket": as_int(state.get("ticket")),
            "paused": paused and {"flow": "ticket", "step": state.get("paused_step"), "ticket": paused}}


def write_state(root, position, paused=None):
    """Write the position, and a paused ticket flow, to the state file in the guide skill's shape."""
    path = Path(root) / STATE
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"flow: {position['flow']}", f"step: {position['step']}"]
    lines += [f"ticket: {position['ticket']}"] if position["ticket"] else []
    lines += [f"paused_ticket: {paused['ticket']}", f"paused_step: {paused['step']}"] if paused else []
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
    """The position: the state file, corrected from the ticket's board column when Gitea answers."""
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
    return position


def unscoped(gitea, ticket):
    """True when the ticket has no Acceptance section (formats, Ticket)."""
    return bool(ticket) and "## Acceptance" not in commands.issue(gitea.call, gitea.repo, ticket)["body"]


def tested(gitea, ticket):
    """True when the ticket carries a Tested Pointer."""
    return any(c["text"].startswith(f"{TESTED}, ") for c in commands.issue(gitea.call, gitea.repo, ticket)["comments"])


def milestone_tested(gitea, ticket):
    """True when every other open ticket in the ticket's milestone is past Testing, or in it with a Tested Pointer."""
    milestone = ticket and commands.issue(gitea.call, gitea.repo, ticket)["milestone"]
    if not milestone:
        return False
    placed = commands.column_tickets(gitea.call, gitea.repo)
    others = {column: [t["number"] for t in placed.get(column, [])
                       if t["milestone"] == milestone and t["number"] != ticket]
              for column in (*BEFORE_TESTING, "Testing")}
    if any(others[column] for column in BEFORE_TESTING):
        return False
    return all(commands.each(lambda n: tested(gitea, n), others["Testing"]))


CHECKS = {"unscoped": unscoped, "milestone_tested": milestone_tested}


def checks(gitea, position, prompts):
    """holds(check) for a fork's `when` at this position; a check Gitea cannot answer holds, so the person decides."""
    def holds(check):
        try:
            with prompts.busy("Checking"):
                return CHECKS[check](gitea, position and position["ticket"])
        except GiteaError:
            return True
    return holds


def show(root, gitea):
    """The position, its environment, any corrections and the choices, as `dp guide --json` prints them."""
    flow_map, notes = flows.load(), Notes()
    state = read_state(root)
    position = locate(flow_map, state, gitea, notes)
    return {"position": position, "env": position and flow_map["steps"][position["step"]]["env"],
            "paused": state and state["paused"], "notes": notes.lines,
            "choices": flows.choices(flow_map, position, checks(gitea, position, notes))}


def header(position, env):
    """The Guide prompt's first line (formats)."""
    if not position:
        return "Guide · start"
    ticket = f" · #{position['ticket']}" if position["ticket"] else ""
    return f"Guide · {position['flow']} flow{ticket} · {position['step']} ({env})"


def label(choice, position):
    """A choice line (formats, Guide prompt): the name, its line, and a flow it switches to."""
    switches = position and choice["flow"] != position["flow"]
    return f"{choice['name']:<11} {choice['does']}" + (f" → {choice['flow']} flow" if switches else "")


def menu(offered, position):
    """The options: this flow's steps; inside a flow, a separator, the forks and `flows…`; then stop.

    At the end of a flow the choices are the flows already, so there is no `flows…`.
    """
    options = [(label(c, position), c) for c in offered if c["kind"] != "fork"]
    if position and offered[0]["kind"] != "flow":
        options += [SEPARATOR, *((label(c, position), c) for c in offered if c["kind"] == "fork"), FLOWS]
    return options + [(STOP, None)]


def guide_prompt(shown):
    """The Guide prompt as text, for a session or a pipe."""
    lines, count = [*shown["notes"], header(shown["position"], shown["env"])], 0
    for text, value in menu(shown["choices"], shown["position"]):
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


def take(gitea, git, ticket, branch):
    """Move the ticket to In Progress (assigning the person), into the open milestone due first when it has
    none, and branch from prep; what happened, as `dp pick --json` prints it."""
    moved = commands.move(gitea.call, gitea.repo, ticket["number"], "In Progress", assignee=gitea.human())
    joined = None if ticket["milestone"] else commands.join_earliest_milestone(gitea.call, gitea.repo, ticket["number"])
    git("switch", f"--create={branch}", BASE)  # one argument, so a leading-dash branch is not an option
    return {**moved, "milestone": joined or ticket["milestone"], "joined": bool(joined), "branch": branch}


def taken_lines(taken):
    at = f"[ticket #{taken['number']}]"
    return [f"{at} {taken['from'] or 'off the Board'} → In Progress · assigned {taken['assigned']}",
            *([f"{at} joined {taken['milestone']}"] if taken["joined"] else []),
            f"{at} branch {taken['branch']} from {BASE}"]


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
    branch = prompts.text("Branch", branch_name(chosen))
    with prompts.busy(f"Moving #{chosen['number']}"):
        taken = take(gitea, git, chosen, branch)
    for line in taken_lines(taken):
        prompts.say(line)
    prompts.say(NEXT_STEP)
    return chosen["number"]


def adjudicate(root, flow, ticket, prompts):
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
        kind = prompts.choose(f"{finding['id']}?", [(f"{name:<9} {hint}", name) for name, hint in DISPOSITIONS.items()])
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


def leave_test(position, prompts, gitea, env):
    """Leaving `test` records the hand test as a Pointer on the ticket; False to stay at `test`."""
    ticket = position["ticket"]
    if not prompts.confirm("Tested OK?"):
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


def merge_state(gitea, git):
    """The current branch's PR as (number, "merged" | "open" | "closed"), or None when it has none or git or Gitea cannot say."""
    try:
        branch = git("branch", "--show-current").strip()
        pulls = commands.paged(gitea.call, f"repos/{gitea.repo}/pulls?state=all")
    except GiteaError:  # `git` raises GiteaError too, so a failing git falls back to asking
        return None
    pull = next((p for p in pulls if p["head"]["ref"] == branch), None)
    if not pull:
        return None
    state = "merged" if pull["merged"] else pull.get("state", "open")
    return pull["number"], state


def confirm_done(step, does, ticket, prompts, gitea, git):
    """True when a person's step is done: `merge` reads the PR's state, any other step asks."""
    pull = merge_state(gitea, git) if step == "merge" else None
    if pull and pull[1] == "merged":
        return True
    if pull and pull[1] == "closed":
        prompts.note(f"{ref('ticket', ticket)} PR #{pull[0]} is closed, not merged · reopen it or open a new one, then run dp guide")
        return False
    if pull:
        prompts.note(f"{ref('ticket', ticket)} PR #{pull[0]} is not merged · merge it, then run dp guide")
        return False
    return prompts.confirm(f"{does}. Done?")


def run(root, flow_map, position, choice, prompts, gitea, git):
    """Run the chosen step; the position it reached, or None when it did not happen."""
    flow, step = choice["flow"], choice["step"]
    ticket = position["ticket"] if position and flow == "ticket" else None
    skill = flow_map["steps"][step]["skill"]
    if step == "pick":
        ticket = pick(prompts, gitea, git)
        if ticket is None:
            return None
    elif step == "finish":
        commands.finish(gitea.call, gitea.repo, ticket)  # the Pointer was posted on leaving `test`
        prompts.say(f"{ref(flow, ticket)} DONE · closed, in DoD")
    elif step == "defect":
        found = prompts.text("What failed", "").strip().rstrip(".") or "a defect at test"
        text = f"{TESTED_DEFECT}, {datetime.now():%Y-%m-%d}. Landed: merged to prep. Left: {found}. → Backlog"
        commands.reopen(gitea.call, gitea.repo, ticket, text)
        prompts.say(f"{ref(flow, ticket)} reopened · Backlog · {found}")
    elif skill == "human":
        does = flow_map["steps"][step]["does"]
        if step == "test":
            prompts.say(LEAVING_TEST)  # leaving `test` asks "Tested OK?", so entering it does not ask "Done?"
        elif step == "sign-off":
            recorded(root, flow, ticket, prompts)  # what the person signs; nothing is asked again
        if step != "test" and not confirm_done(step, does, ticket, prompts, gitea, git):
            return None
        prompts.say(NEXT_STEP)
    elif brief.user_invoked(skill):
        prompts.say(f"Type /datumpin:{skill} in the session you worked in.")
        prompts.say("Next: type it there, then run dp guide")
    else:
        # A tag follows the release PR on main, whatever the state file says (guide skill).
        if step == "tag" and not prompts.confirm("Is the release PR merged on main?"):
            return None
        if step != "review":
            adjudicate(root, flow, ticket, prompts)  # findings a resumed walk passed by undecided
        work = job(flow_map, flow, step, ticket, gitea, git, prompts)
        if flow == "release" and step == "review" and not work.diffstat.strip():
            raise GiteaError(f"empty diff {PROMOTION}: nothing to review, no findings written")
        path = brief.write(root, work)
        model = brief.skill_header(skill)
        prompts.say(f"{ref(flow, ticket)} Claude · {work.does} · /exit returns to the guide")
        prompts.job(brief.prompt(work, path.relative_to(root)), model.get("model"), model.get("effort"))
    return {"flow": flow, "step": step, "ticket": ticket}


def choose_flow(flow_map, paused, prompts):
    resume = [(f"{'resume':<11} #{paused['ticket']} at {paused['step']}", "resume")] if paused else []
    return prompts.choose("Flow?", resume + [(label(c, None), c) for c in flows.flow_starts(flow_map)]
                          + [(BACK, None)])


def may_leave(position, here, choice, prompts, gitea):
    """Leaving a step: `test` needs its Tested Pointer first, unless a defect reopens it; False to stay."""
    if position and position["step"] == "test" and position["ticket"] and choice["step"] != "defect":
        return leave_test(position, prompts, gitea, here["env"])
    return True


def still_paused(position, reached, paused):
    """The paused ticket flow after a step: set on leaving the ticket flow, cleared on coming back to it."""
    if reached["flow"] == "ticket":
        return None
    if position and position["flow"] == "ticket" and position["ticket"]:
        return position
    return paused


def walk(root, prompts, gitea, git):
    """Offer the next steps and run each choice, until the person stops."""
    root, flow_map = Path(root), flows.load()
    state = read_state(root)
    paused = state and state["paused"]
    position = locate(flow_map, state, gitea, prompts)
    while True:
        # A review's dispositions come before the menu, so they can preselect fix or pr.
        preselect = position and position["step"] == "review" \
            and adjudicate(root, position["flow"], position["ticket"], prompts)
        here = position and flow_map["steps"][position["step"]]
        prompts.header(position, here and here["env"], position and flows.rail(flow_map, position),
                       here and here["does"])
        options = menu(flows.choices(flow_map, position, checks(gitea, position, prompts)), position)
        default = next((v for _, v in options if isinstance(v, dict) and v["step"] == preselect), None)
        choice = prompts.choose("Next?", options, default)
        if choice is None:
            break
        if choice == "flows":
            choice = choose_flow(flow_map, paused, prompts)
            if choice == "resume":
                position, paused = locate(flow_map, paused, gitea, prompts), None
            if not isinstance(choice, dict):
                continue
        if not may_leave(position, here, choice, prompts, gitea):
            continue
        reached = run(root, flow_map, position, choice, prompts, gitea, git)
        if reached:
            position, paused = reached, still_paused(position, reached, paused)
            write_state(root, position, paused)
    if position:
        write_state(root, position, paused)
        prompts.outro(f"{ref(position['flow'], position['ticket'])} stopped · resume at {position['step']} · dp guide")
    else:
        prompts.outro("[guide] stopped")
