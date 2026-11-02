"""The flow map: where the work stands and what may come next.

Summary: the position from the state file and a ticket's board column, the
         choices from that position, and the rail: the flow's usual path.
Input:   flows.yaml, packaged with dp from the plugin; a state as
         {flow, step, ticket}.
Output:  plain dicts, as `dp guide --json` prints them.
"""

import yaml

from dp import data


def load():
    """The flow map that shipped with this dp."""
    return yaml.safe_load(data("flows.yaml").read_text(encoding="utf-8"))


def known(flow_map, state):
    """True when the map has the state's flow and lists its step in that flow."""
    return bool(state) and state.get("flow") in flow_map["flows"] \
        and state.get("step") in flow_map["flows"][state["flow"]]["steps"]


def position(flow_map, state, column):
    """(position, corrected): the state, unless the ticket's column places it elsewhere.

    Process: only the ticket flow follows a column; a column's `keep` steps
    stand, any other state step moves to the column's step. A flow other than
    the ticket flow carries no ticket. A state the map does not know has no
    position.
    """
    if not known(flow_map, state):
        return None, False
    if state["flow"] != "ticket" or column not in flow_map["columns"]:
        return state, False
    rule = flow_map["columns"][column]
    if state["step"] in rule.get("keep", []):
        return state, False
    flow = rule.get("flow", "ticket")
    placed = {"flow": flow, "step": rule["step"], "ticket": state.get("ticket") if flow == "ticket" else None}
    return placed, placed != state


def flow_of(flow_map, flow, step):
    """The flow a step continues in: this one when it lists the step, else the first that does."""
    if step in flow_map["flows"][flow]["steps"]:
        return flow
    return next(name for name, listed in flow_map["flows"].items() if step in listed["steps"])


def forks(defined):
    """A step's forks as (step, check): a fork names a step, or a step and the check that must hold."""
    return [(target, None) if isinstance(target, str) else (target["step"], target["when"])
            for target in defined.get("fork", {}).values()]


def flow_starts(flow_map):
    """Each flow at its first step, as choices."""
    return [{"name": name, "step": listed["steps"][0], "flow": name, "does": listed["does"], "kind": "flow"}
            for name, listed in flow_map["flows"].items()]


def choices(flow_map, position, holds=lambda check: True, pending=False):
    """What may come next: the step's `next` and `optional` steps its flow lists, then the forks that hold.

    Without a position, or at the end of a flow, each flow at its first step.
    `name` is what the menu shows: the step, or the flow it starts; `kind`
    is `next`, `fork` or `flow`. holds(check) answers a fork's `when`.
    A `pending` position is a step that has not run, so it is offered first.
    """
    offered = []
    if position:
        flow, step = position["flow"], flow_map["steps"][position["step"]]
        listed = flow_map["flows"][flow]["steps"]
        following = [s for s in step.get("next", []) + step.get("optional", []) if s in listed]
        offered = [{"name": s, "step": s, "flow": flow, "does": flow_map["steps"][s]["does"], "kind": "next"}
                   for s in dict.fromkeys(([position["step"]] if pending else []) + following)]
        offered += [{"name": s, "step": s, "flow": flow_of(flow_map, flow, s),
                     "does": flow_map["steps"][s]["does"], "kind": "fork"}
                    for s, check in forks(step) if check is None or holds(check)]
    return offered or flow_starts(flow_map)


def leads_to(flow_map, step):
    defined = flow_map["steps"][step]
    return defined.get("next", []) + defined.get("optional", []) + [s for s, _ in forks(defined)]


def path(flow_map, flow):
    """A flow's usual path: its first step, then each step's first `next` the flow lists."""
    listed = flow_map["flows"][flow]["steps"]
    steps = [listed[0]]
    while following := [s for s in flow_map["steps"][steps[-1]].get("next", []) if s in listed and s not in steps]:
        steps.append(following[0])
    return steps


def rail(flow_map, position):
    """The usual path as (step, done | current | next); a step off it follows the step leading to it."""
    steps, current = path(flow_map, position["flow"]), position["step"]
    if current not in steps:
        leading = [n for n, step in enumerate(steps) if current in leads_to(flow_map, step)]
        steps.insert(leading[0] + 1 if leading else 0, current)
    at = steps.index(current)
    return [(step, "done" if n < at else "current" if n == at else "next") for n, step in enumerate(steps)]
