"""dp's job briefs: what an agent needs for one step, gathered before its session.

Summary: writes .factory/jobs/<ticket, or flow>/<step>.md and the prompt to
         paste into a session.
Input:   a Job (the step, the ticket with its comments and column, the diff
         stat, the skill text) and the skills packaged with dp.
Output:  the brief and its prompt. A review brief asks for findings.json
         beside it; a later brief lists those findings with the dispositions
         `dp guide` asked the person for.
"""
import json
import re
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

FINDINGS = "findings.json"
NO_SKILL_FILE = ("agent", "human")
HEADING = re.compile(r"(#{1,6}) (.+)")
FENCE = re.compile(r"\s*```")
ASK_FINDINGS = (
    "Write the findings to `{path}` as a JSON list, one object per finding: "
    '`{{"id": "S1", "file": "a.py", "line": 3, "severity": "low", "finding": "<one line>"}}`, '
    "with ids numbered as `formats` (Pull request) numbers them, or `[]` with none. "
    "Write no dispositions: `dp guide` asks the person for each one.")
ACT_ON_FINDINGS = (
    "Act on each disposition: `Fix` is fixed in this step and becomes `Fixed (<sha>)`; `Defer` "
    "becomes `Deferred: #N`, with N a Triage ticket opened for it; the others stand as written.")


@dataclass
class Job:
    flow: str
    step: str
    does: str
    env: str
    ticket: dict | None  # number, title, body, comments as [{author, text}]
    column: str | None
    diffstat: str
    skills: str


def folder(root, ticket, flow):
    """Where a ticket's (or a ticketless flow's) briefs and findings live."""
    return Path(root) / ".factory" / "jobs" / str(ticket or flow)


def split_skill(name):
    """A packaged skill's frontmatter and body."""
    text = (files("dp") / "data" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
    head, _, body = text.removeprefix("---\n").partition("\n---\n")
    return head, body.strip()


def user_invoked(skill):
    """True for a skill only the person starts (handoff, retro): typed in a session, never briefed."""
    return skill not in NO_SKILL_FILE and "disable-model-invocation: true" in split_skill(skill)[0]


def section(markdown, heading):
    """A heading's section: its line up to the next heading of its level or higher, outside code."""
    kept, level, fenced = [], None, False
    for line in markdown.splitlines():
        found = None if fenced else HEADING.fullmatch(line)
        if FENCE.match(line):
            fenced = not fenced
        if found and level and len(found.group(1)) <= level:
            break
        if found and not level and found.group(2).strip() == heading:
            level = len(found.group(1))
        if level:
            kept.append(line)
    if not kept:
        raise LookupError(f"no heading {heading!r}")
    return "\n".join(kept).strip()


def skill_text(step):
    """The skill text a step's brief carries: its `brief` sections, else its whole skill."""
    if "brief" in step:
        return "\n\n".join(section(split_skill(name)[1], heading)
                           for name, heading in (entry.split("#", 1) for entry in step["brief"]))
    return "" if step["skill"] in NO_SKILL_FILE else split_skill(step["skill"])[1]


def findings_table(findings):
    rows = [f"| {f['id']} | {f['file']}:{f['line']} {f['finding']} | {f['severity']} | {f.get('disposition', '')} |"
            for f in findings]
    return "\n".join(["| # | Finding | Sev | Disposition |", "|---|---|---|---|", *rows])


def render(job, findings, findings_path):
    ticket = job.ticket
    title = f"#{ticket['number']} {ticket['title']}" if ticket else f"the {job.flow} flow"
    where = f"Flow `{job.flow}`, environment `{job.env}`" + (f", board column {job.column}" if job.column else "")
    parts = [f"# Step {job.step}: {title}", f"{job.does}. {where}.",
             "This brief carries what the step needs, its skill text included: do not load that skill "
             "again. Print in the `formats` shapes, and stop when the step is done."]
    if ticket:
        comments = "\n\n".join(f"**{c['author']}:** {c['text'].strip()}" for c in ticket["comments"])
        parts += ["## Ticket", ticket["body"].strip() or "(no body)", "## Comments", comments or "(none)"]
    parts += ["## Diff stat", f"```\n{job.diffstat.strip() or '(no changes against prep)'}\n```"]
    if job.step == "review":
        parts += ["## Findings", ASK_FINDINGS.format(path=findings_path)]
    elif findings:
        parts += ["## Findings", findings_table(findings), ACT_ON_FINDINGS]
    if job.skills:
        parts += ["---", job.skills]
    return "\n\n".join(parts) + "\n"


def write(root, job):
    """Write the job's brief and return its path."""
    root = Path(root)
    jobs = folder(root, job.ticket and job.ticket["number"], job.flow)
    jobs.mkdir(parents=True, exist_ok=True)
    found = jobs / FINDINGS
    findings = json.loads(found.read_text(encoding="utf-8")) if found.is_file() else None
    path = jobs / f"{job.step}.md"
    text = render(job, findings, found.relative_to(root).as_posix())
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def prompt(job, path):
    """The prompt to paste into a session; `dp tokens` books the turns after it to the step."""
    owner = f"#{job.ticket['number']}" if job.ticket else f"the {job.flow} flow"
    return f"Step {job.step} of {owner}: read {Path(path).as_posix()} and do it."
