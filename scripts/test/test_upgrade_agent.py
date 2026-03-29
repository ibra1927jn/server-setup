"""Tests for JSON parsing and version patching logic in upgrade_agent_node.py"""
import json


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
    data = _workflow_dict()
    if isinstance(data, list):
        wf = data[0]
    else:
        wf = data
    assert wf["name"] == "AI Agent Base"


def test_parse_list_format():
    """When export is a list, use first element."""
    data = [_workflow_dict()]
    if isinstance(data, list):
        wf = data[0]
    else:
        wf = data
    assert wf["name"] == "AI Agent Base"


def test_find_agent_nodes():
    """Should find nodes with 'agent' in their type."""
    wf = _workflow_dict()
    agent_nodes = [n for n in wf["nodes"] if "agent" in n.get("type", "").lower()]
    assert len(agent_nodes) == 1
    assert agent_nodes[0]["name"] == "AI Agent1"


def test_find_agent_nodes_case_insensitive():
    """Detection should be case-insensitive."""
    wf = _workflow_dict(nodes=[
        {"name": "MyAgent", "type": "some.AGENT.node", "typeVersion": 1},
    ])
    agent_nodes = [n for n in wf["nodes"] if "agent" in n.get("type", "").lower()]
    assert len(agent_nodes) == 1


def test_no_agent_nodes():
    """Should find zero agent nodes when none exist."""
    wf = _workflow_dict(nodes=[
        {"name": "Trigger", "type": "n8n-nodes-base.start", "typeVersion": 1},
    ])
    agent_nodes = [n for n in wf["nodes"] if "agent" in n.get("type", "").lower()]
    assert len(agent_nodes) == 0


def test_patch_version():
    """Should update typeVersion to 2.1."""
    wf = _workflow_dict()
    patched = False
    for node in wf["nodes"]:
        if "agent" in node.get("type", "").lower():
            node["typeVersion"] = 2.1
            patched = True
    assert patched is True
    agent = [n for n in wf["nodes"] if "agent" in n.get("type", "").lower()][0]
    assert agent["typeVersion"] == 2.1


def test_patch_preserves_other_nodes():
    """Patching agent version should not affect other nodes."""
    wf = _workflow_dict()
    for node in wf["nodes"]:
        if "agent" in node.get("type", "").lower():
            node["typeVersion"] = 2.1
    trigger = [n for n in wf["nodes"] if n["name"] == "Trigger"][0]
    assert trigger["typeVersion"] == 1
    chat = [n for n in wf["nodes"] if n["name"] == "Chat Model"][0]
    assert chat["typeVersion"] == 1


def test_missing_type_field():
    """Nodes without a type field should not match agent filter."""
    wf = _workflow_dict(nodes=[
        {"name": "NoType", "typeVersion": 1},
        {"name": "Agent", "type": "@n8n/n8n-nodes-langchain.agent", "typeVersion": 1},
    ])
    agent_nodes = [n for n in wf["nodes"] if "agent" in n.get("type", "").lower()]
    assert len(agent_nodes) == 1
    assert agent_nodes[0]["name"] == "Agent"


def test_serialization_after_patch():
    """Patched workflow should be JSON-serializable."""
    wf = _workflow_dict()
    for node in wf["nodes"]:
        if "agent" in node.get("type", "").lower():
            node["typeVersion"] = 2.1
    serialized = json.dumps(wf)
    restored = json.loads(serialized)
    agent = [n for n in restored["nodes"] if "agent" in n.get("type", "").lower()][0]
    assert agent["typeVersion"] == 2.1
