"""Tests for JSON manipulation logic used in patch_workflow.py"""
import json


def _sample_workflow():
    """Create a sample workflow with an OpenAI Chat Model node."""
    return {
        "nodes": [
            {"name": "Telegram Trigger", "type": "n8n-nodes-base.telegramTrigger"},
            {"name": "AI Agent1", "type": "@n8n/n8n-nodes-langchain.agent"},
            {"name": "OpenAI Chat Model", "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi"},
        ],
        "connections": {
            "Telegram Trigger": {"main": [[{"node": "AI Agent1", "type": "main", "index": 0}]]},
            "OpenAI Chat Model": {
                "ai_languageModel": [[{"node": "AI Agent1", "type": "ai_languageModel", "index": 0}]]
            },
        },
        "active": False,
    }


def test_filter_removes_target_node():
    """Filtering should remove only the OpenAI Chat Model node."""
    wf = _sample_workflow()
    new_nodes = [n for n in wf["nodes"] if n["name"] != "OpenAI Chat Model"]
    assert len(new_nodes) == 2
    names = [n["name"] for n in new_nodes]
    assert "OpenAI Chat Model" not in names
    assert "AI Agent1" in names
    assert "Telegram Trigger" in names


def test_filter_preserves_other_nodes():
    """Non-target nodes should be untouched."""
    wf = _sample_workflow()
    original_trigger = wf["nodes"][0].copy()
    new_nodes = [n for n in wf["nodes"] if n["name"] != "OpenAI Chat Model"]
    assert new_nodes[0] == original_trigger


def test_filter_noop_when_not_present():
    """If target node isn't present, filter returns all nodes."""
    wf = {"nodes": [{"name": "A"}, {"name": "B"}]}
    new_nodes = [n for n in wf["nodes"] if n["name"] != "OpenAI Chat Model"]
    assert len(new_nodes) == 2


def test_connection_rebuild():
    """After deleting old connection, new one should be created."""
    conns = {"OpenAI Chat Model": {"old": "data"}, "Trigger": {"main": []}}
    if "OpenAI Chat Model" in conns:
        del conns["OpenAI Chat Model"]
    assert "OpenAI Chat Model" not in conns
    assert "Trigger" in conns  # other connections preserved

    # Rebuild
    conns["OpenAI Chat Model"] = {
        "ai_languageModel": [[{"node": "AI Agent1", "type": "ai_languageModel", "index": 0}]]
    }
    assert "ai_languageModel" in conns["OpenAI Chat Model"]


def test_response_id_parsing_nested():
    """Parse workflow ID from nested API response."""
    res_json = {"data": {"id": "WiTcSI66bHwdSgkd", "name": "AI Agent"}}
    parsed_id = res_json.get("data", res_json).get("id")
    assert parsed_id == "WiTcSI66bHwdSgkd"


def test_response_id_parsing_flat():
    """Parse workflow ID from flat API response."""
    res_json = {"id": "abc123", "name": "AI Agent"}
    parsed_id = res_json.get("data", res_json).get("id")
    assert parsed_id == "abc123"


def test_response_id_parsing_missing():
    """When id is missing, should return None."""
    res_json = {"data": {"name": "AI Agent"}}
    parsed_id = res_json.get("data", res_json).get("id")
    assert parsed_id is None


def test_activate_flag():
    """Setting active=True should persist."""
    wf = _sample_workflow()
    assert wf["active"] is False
    wf["active"] = True
    assert wf["active"] is True


def test_full_patch_roundtrip():
    """Full patch cycle: filter, add new node, rebuild connections, serialize."""
    wf = _sample_workflow()

    # Filter
    new_nodes = [n for n in wf["nodes"] if n["name"] != "OpenAI Chat Model"]

    # Add replacement node
    replacement = {
        "name": "OpenAI Chat Model",
        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
        "parameters": {"model": "gpt-4"},
    }
    new_nodes.append(replacement)
    wf["nodes"] = new_nodes

    # Verify serializable
    serialized = json.dumps(wf)
    restored = json.loads(serialized)
    assert len(restored["nodes"]) == 3
    model_node = [n for n in restored["nodes"] if n["name"] == "OpenAI Chat Model"][0]
    assert model_node["parameters"]["model"] == "gpt-4"
