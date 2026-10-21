"""The flow map: where the work stands and what may come next.

Summary: the position from the state file and a ticket's board column, and
         the choices from that position.
Input:   flows.yaml, packaged with dp from the plugin; a state as
         {flow, step, ticket}.
Output:  plain dicts, as `dp guide --json` prints them.
"""
from importlib.resources import files

import yaml


def load():
    """The flow map that shipped with this dp."""
    return yaml.safe_load((files("dp") / "data" / "flows.yaml").read_text(encoding="utf-8"))


def known(flow_map, state):
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


def choices(flow_map, position):
    """What may come next: the step's `next` and `optional` steps its flow lists, then its forks.

    Without a position, or at the end of a flow, each flow at its first step.
    `name` is what the menu shows: the step, or the flow it starts.
    """
    offered = []
    if position:
        flow, step = position["flow"], flow_map["steps"][position["step"]]
        listed = flow_map["flows"][flow]["steps"]
        following = [s for s in step.get("next", []) + step.get("optional", []) if s in listed]
        offered = [{"name": s, "step": s, "flow": flow, "does": flow_map["steps"][s]["does"]}
                   for s in dict.fromkeys(following)]
        offered += [{"name": s, "step": s, "flow": flow_of(flow_map, flow, s),
                     "does": flow_map["steps"][s]["does"]} for s in step.get("fork", {}).values()]
    return offered or [{"name": name, "step": listed["steps"][0], "flow": name, "does": listed["does"]}
                       for name, listed in flow_map["flows"].items()]
