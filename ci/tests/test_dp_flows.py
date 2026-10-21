"""Unit tier: dp's flow map (plugins/datumpin/flows.yaml) and dp.flows, which reads it."""
import pytest

from dp import flows
from fake_gitea import COLUMNS


@pytest.fixture(scope="module")
def flow_map():
    return flows.load()


def state(step, flow="ticket", ticket=4):
    return {"flow": flow, "step": step, "ticket": ticket}


def steps_of(choices):
    return [choice["step"] for choice in choices]


@pytest.mark.unit
def test_every_board_column_places_a_ticket_on_a_step_its_flow_lists(flow_map):
    for column in COLUMNS:
        rule = flow_map["columns"][column]
        listed = flow_map["flows"][rule.get("flow", "ticket")]["steps"]
        assert rule["step"] in listed
        assert set(rule.get("keep", [])) <= set(listed)


@pytest.mark.unit
def test_every_step_a_flow_names_is_defined(flow_map):
    for flow in flow_map["flows"].values():
        for step in flow["steps"]:
            defined = flow_map["steps"][step]
            assert set(defined.get("next", []) + defined.get("optional", [])) <= set(flow_map["steps"])
            assert set(defined.get("fork", {}).values()) <= set(flow_map["steps"])


@pytest.mark.unit
def test_the_column_corrects_a_state_step_it_does_not_keep(flow_map):
    assert flows.position(flow_map, state("review"), "Backlog") == (state("pick"), True)


@pytest.mark.unit
def test_in_progress_keeps_a_state_step_from_build_to_fix(flow_map):
    assert flows.position(flow_map, state("commit"), "In Progress") == (state("commit"), False)


@pytest.mark.unit
def test_dod_moves_to_the_release_flow_without_a_ticket(flow_map):
    assert flows.position(flow_map, state("try"), "DoD") == (state("review", "release", None), True)


@pytest.mark.unit
def test_without_a_column_the_state_stands(flow_map):
    assert flows.position(flow_map, state("tag", "release", None), None) == (state("tag", "release", None), False)


@pytest.mark.unit
@pytest.mark.parametrize("unknown", [None, state("nope", "ticket"), state("pick", "nope"), state("tag")])
def test_a_state_the_map_does_not_know_has_no_position(flow_map, unknown):
    assert flows.position(flow_map, unknown, "Backlog") == (None, False)


@pytest.mark.unit
def test_choices_are_the_next_and_optional_steps_the_flow_lists(flow_map):
    assert steps_of(flows.choices(flow_map, state("review"))) == ["fix", "pr"]
    assert steps_of(flows.choices(flow_map, state("build"))) == ["check", "diagnose"]


@pytest.mark.unit
def test_a_fork_into_another_flow_names_it(flow_map):
    offered = flows.choices(flow_map, state("try"))

    assert [(c["step"], c["flow"]) for c in offered] == [
        ("pick", "ticket"), ("gate", "release"), ("board", "session")]
    assert offered[0]["does"] == flow_map["steps"]["pick"]["does"]


@pytest.mark.unit
def test_without_a_position_each_flow_is_offered_at_its_first_step(flow_map):
    offered = flows.choices(flow_map, None)

    assert [(c["flow"], c["step"]) for c in offered][:2] == [("ticket", "pick"), ("release", "gate")]
    assert offered[0]["does"] == flow_map["flows"]["ticket"]["does"]


@pytest.mark.unit
def test_a_finished_flow_offers_the_flows(flow_map):
    assert flows.choices(flow_map, state("retro", "session", None)) == flows.choices(flow_map, None)
