"""Tests for upgrade_agent_node.py functions"""
import json

from upgrade_agent_node import parse_workflow, patch_agent_nodes


def _workflow_dict(nodes=None):
    """Create a sample workflow as a dict."""
    return {
        "name": "AI Agent Base",
        "nodes": nodes or [
            {"name": "Trigger", "type": "n8n-nodes-base.telegramTrigger", "typeVersion": 1},
            {"name": "AI Agent1", "type": "@n8n/n8n-nodes-langchain.agent", "typeVersion": 1.6},
            {"name": "Chat Model", "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi", "typeVersion": 1},
        ],
    }


def test_parse_dict_format():
    """When export is a dict, use it directly."""
    raw = json.dumps(_workflow_dict())
    wf = parse_workflow(raw)
    assert wf["name"] == "AI Agent Base"


def test_parse_list_format():
    """When export is a list, use first element."""
    raw = json.dumps([_workflow_dict()])
    wf = parse_workflow(raw)
    assert wf["name"] == "AI Agent Base"


def test_parse_list_multiple_elements():
    """When export is a list with multiple, use first element."""
    raw = json.dumps([_workflow_dict(), {"name": "Second"}])
    wf = parse_workflow(raw)
    assert wf["name"] == "AI Agent Base"


def test_patch_agent_nodes_basic():
    """Should patch agent nodes to 2.1."""
    wf = _workflow_dict()
    assert patch_agent_nodes(wf) is True
    agent = [n for n in wf["nodes"] if "agent" in n["type"].lower()][0]
    assert agent["typeVersion"] == 2.1


def test_patch_agent_nodes_custom_version():
    """Should use custom target version."""
    wf = _workflow_dict()
    patch_agent_nodes(wf, target_version=3.0)
    agent = [n for n in wf["nodes"] if "agent" in n["type"].lower()][0]
    assert agent["typeVersion"] == 3.0


def test_patch_agent_preserves_other_nodes():
    """Patching should not affect non-agent nodes."""
    wf = _workflow_dict()
    patch_agent_nodes(wf)
    trigger = [n for n in wf["nodes"] if n["name"] == "Trigger"][0]
    assert trigger["typeVersion"] == 1
    chat = [n for n in wf["nodes"] if n["name"] == "Chat Model"][0]
    assert chat["typeVersion"] == 1


def test_patch_no_agent_returns_false():
    """Should return False when no agent nodes exist."""
    wf = _workflow_dict(nodes=[
        {"name": "Trigger", "type": "n8n-nodes-base.start", "typeVersion": 1},
    ])
    assert patch_agent_nodes(wf) is False


def test_patch_empty_nodes():
    wf = {"nodes": []}
    assert patch_agent_nodes(wf) is False


def test_patch_missing_nodes_key():
    wf = {}
    assert patch_agent_nodes(wf) is False


def test_patch_multiple_agents():
    """Should patch all agent nodes."""
    wf = _workflow_dict(nodes=[
        {"name": "Agent1", "type": "langchain.agent", "typeVersion": 1.0},
        {"name": "Agent2", "type": "custom.agent.v2", "typeVersion": 1.5},
    ])
    assert patch_agent_nodes(wf) is True
    assert wf["nodes"][0]["typeVersion"] == 2.1
    assert wf["nodes"][1]["typeVersion"] == 2.1


def test_patch_case_insensitive():
    """Detection should be case-insensitive."""
    wf = _workflow_dict(nodes=[
        {"name": "MyAgent", "type": "some.AGENT.node", "typeVersion": 1},
    ])
    assert patch_agent_nodes(wf) is True


def test_missing_type_field():
    """Nodes without type should not match."""
    wf = _workflow_dict(nodes=[
        {"name": "NoType", "typeVersion": 1},
    ])
    assert patch_agent_nodes(wf) is False


def test_serialization_after_patch():
    """Patched workflow should be JSON-serializable."""
    wf = _workflow_dict()
    patch_agent_nodes(wf)
    serialized = json.dumps(wf)
    restored = json.loads(serialized)
    agent = [n for n in restored["nodes"] if "agent" in n.get("type", "").lower()][0]
    assert agent["typeVersion"] == 2.1
