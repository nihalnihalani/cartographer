"""Agent-tree construction — must pass with no API key and no database."""

from cartographer.agent import (
    expedition,
    historian,
    mapmaker,
    navigator,
    root_agent,
    surgeon,
    surveyors,
)
from naive_agent.agent import root_agent as naive


def test_tree_shape():
    assert root_agent.name == "cartographer"
    assert [a.name for a in root_agent.sub_agents] == ["expedition", "navigator", "surgeon"]
    assert [a.name for a in expedition.sub_agents] == ["surveyors", "historian", "mapmaker"]
    assert [a.name for a in surveyors.sub_agents] == [
        "surveyor_orders",
        "surveyor_customers",
        "surveyor_products",
    ]


def test_models():
    for a in [root_agent, navigator, surgeon, historian, mapmaker, naive]:
        assert "gemini" in str(a.model)


def _mcp_args(agent):
    return agent.tools[0]._connection_params.server_params.args


def test_tool_filters_least_privilege():
    assert set(surveyors.sub_agents[0].tools[0].tool_filter) == {
        "collection-schema", "aggregate", "count",
    }
    assert set(historian.tools[0].tool_filter) == {"aggregate", "find"}
    assert set(mapmaker.tools[0].tool_filter) == {
        "create-collection", "insert-many", "create-index",
    }
    assert set(navigator.tools[0].tool_filter) == {"find", "aggregate", "explain"}
    assert "update-many" in surgeon.tools[0].tool_filter
    assert root_agent.tools[0].tool_filter == ["list-databases"]


def test_read_only_everywhere_except_writers():
    for a in [root_agent, historian, navigator, naive, *surveyors.sub_agents]:
        assert "--readOnly" in _mcp_args(a), f"{a.name} must be read-only"
    for a in [mapmaker, surgeon]:
        assert "--readOnly" not in _mcp_args(a), f"{a.name} needs the write instance"


def test_surgeon_gate_is_in_instruction():
    text = surgeon.instruction.lower()
    assert "approval" in text and "never propose and execute in the same turn" in text


def test_naive_agent_is_actually_naive():
    text = naive.instruction.lower()
    assert "defensive" in text  # told NOT to be
    assert "do not inspect schemas" in text
