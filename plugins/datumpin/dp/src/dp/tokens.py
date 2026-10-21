"""dp tokens: token usage per flow step, read from one Claude Code session log.

Summary: books each turn's usage to a flow step.
Input:   the lines of a session log (~/.claude/projects/<project>/<session>.jsonl).
Process: a turn is one API response; the log writes one line per content block
         and repeats the response's usage on each, so lines sharing a message id
         are one turn. A state write is a Write or Edit of .factory/guide.yaml,
         or a shell command redirecting into it; when the log has one, a turn
         belongs to the step the next write names, otherwise a step starts at
         each Skill call.
Output:  one row per step (turns, tools, input, cache_read, cache_write, output)
         and, as text, a TOTAL row.
"""
import json
import re

STATE_FILE = ".factory/guide.yaml"
STATE_REDIRECT = re.compile(r">\s*[\"']?[^\s\"'|;&]*" + re.escape(STATE_FILE))
STEP = re.compile(r"step: ([\w-]+)")
COUNTS = ("turns", "tools", "input", "cache_read", "cache_write", "output")
USAGE = {"input": "input_tokens", "cache_read": "cache_read_input_tokens",
         "cache_write": "cache_creation_input_tokens", "output": "output_tokens"}


def turns(lines):
    """Assistant turns in log order, as (usage, tool_use blocks)."""
    by_id = {}
    for number, line in enumerate(lines):
        entry = json.loads(line)
        if entry.get("type") != "assistant":
            continue
        message = entry["message"]
        turn = by_id.setdefault(message.get("id") or number, (message.get("usage", {}), []))
        turn[1].extend(block for block in message["content"] if block.get("type") == "tool_use")
    return list(by_id.values())


def written_text(tool):
    """What a tool call writes to the guide's state file, or None."""
    given = tool["input"]
    if tool["name"] in ("Write", "Edit"):
        if given.get("file_path", "").replace("\\", "/").endswith(STATE_FILE):
            return given.get("content", given.get("new_string"))
    elif tool["name"] in ("Bash", "PowerShell"):
        command = given.get("command", "")
        if STATE_REDIRECT.search(command.replace("\\", "/")):
            return command
    return None


def state_write(tools):
    """The step a turn's tool calls last write to the guide's state file, or None."""
    named = None
    for tool in tools:
        found = STEP.findall(written_text(tool) or "")
        named = found[-1] if found else named
    return named


def steps(log):
    """The step each turn is booked to.

    Process: with any state write in the log, walk back from the last one so
    each turn takes the step its next write names, and turns after the last
    write keep that step. Without one, a step starts at each Skill call, and
    the turns before the first call are "start".
    """
    written = [state_write(tools) for _, tools in log]
    if any(written):
        booked, step = [], next(name for name in reversed(written) if name)
        for name in reversed(written):
            step = name or step
            booked.append(step)
        return booked[::-1]
    booked, step = [], "start"
    for _, tools in log:
        step = next((tool["input"]["skill"] for tool in tools if tool["name"] == "Skill"), step)
        booked.append(step)
    return booked


def report(lines):
    """One row per step, in the order the steps first appear."""
    log = turns(lines)
    rows = {}
    for (usage, tools), step in zip(log, steps(log)):
        row = rows.setdefault(step, {"step": step, **dict.fromkeys(COUNTS, 0)})
        row["turns"] += 1
        row["tools"] += len(tools)
        for count, field in USAGE.items():
            row[count] += usage.get(field) or 0
    return list(rows.values())


def table(rows):
    """The rows and their TOTAL as aligned text."""
    total = {"step": "TOTAL", **{count: sum(row[count] for row in rows) for count in COUNTS}}
    width = max(len(row["step"]) for row in rows + [total])
    lines = [f"{'step':<{width}}" + "".join(f"{count:>12}" for count in COUNTS)]
    lines += [f"{row['step']:<{width}}" + "".join(f"{row[count]:>12}" for count in COUNTS)
              for row in rows + [total]]
    return "\n".join(lines)
