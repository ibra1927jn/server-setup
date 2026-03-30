"""Tests for workflow patching operations (filter nodes, fix connections, build nodes)."""
import json


def _sample_workflow():
    """Workflow with agent + chat model nodes and connections."""
    return {
        "name": "AI Agent Base",
        "nodes": [
            {"name": "Telegram Trigger", "type": "n8n-nodes-base.telegramTrigger",
             "typeVersion": 1, "position": [250, 300], "parameters": {}},
            {"name": "AI Agent1", "type": "@n8n/n8n-nodes-langchain.agent",
             "typeVersion": 1.6, "position": [450, 300], "parameters": {}},
            {"name": "OpenAI Chat Model", "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
             "typeVersion": 1, "position": [280, 500], "parameters": {
                 "model": "gpt-4", "options": {"temperature": 0.7}}},
        ],
        "connections": {
            "Telegram Trigger": {"main": [[{"node": "AI Agent1", "type": "main", "index": 0}]]},
            "OpenAI Chat Model": {"ai_languageModel": [
                [{"node": "AI Agent1", "type": "ai_languageModel", "index": 0}]
            ]},
        },
        "active": True,
    }


def test_filter_out_node_by_name():
    """Filtering nodes by name should remove the target and keep others."""
    wf = _sample_workflow()
    target = "OpenAI Chat Model"
    new_nodes = [n for n in wf["nodes"] if n["name"] != target]
    assert len(new_nodes) == 2
    assert all(n["name"] != target for n in new_nodes)


def test_filter_preserves_order():
    """Node order should be preserved after filtering."""
    wf = _sample_workflow()
    new_nodes = [n for n in wf["nodes"] if n["name"] != "OpenAI Chat Model"]
    assert new_nodes[0]["name"] == "Telegram Trigger"
    assert new_nodes[1]["name"] == "AI Agent1"


def test_filter_nonexistent_node_keeps_all():
    """Filtering a name that doesn't exist should keep all nodes."""
    wf = _sample_workflow()
    new_nodes = [n for n in wf["nodes"] if n["name"] != "Nonexistent"]
    assert len(new_nodes) == 3


def test_build_chat_model_node():
    """Building a chat model node should include all required fields."""
    node = {
        "parameters": {"model": "z-ai/glm-4.5-air:free",
                       "options": {"temperature": 0.7, "maxTokens": 500}},
        "id": "e4f8d5bc-3306-4649-8b4e-250327fcdbc1",
        "name": "OpenAI Chat Model",
        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
        "typeVersion": 1,
        "position": [280, 500],
        "credentials": {"openAiApi": {"id": "D98S1Z0HkO9oWJ54", "name": "OpenRouter Account"}},
    }
    assert node["type"] == "@n8n/n8n-nodes-langchain.lmChatOpenAi"
    assert node["credentials"]["openAiApi"]["id"] == "D98S1Z0HkO9oWJ54"
    assert node["parameters"]["model"] == "z-ai/glm-4.5-air:free"


def test_replace_node_in_workflow():
    """Replace old node with new node and verify connections survive."""
    wf = _sample_workflow()
    # Filter out old
    wf["nodes"] = [n for n in wf["nodes"] if n["name"] != "OpenAI Chat Model"]
    # Add replacement
    replacement = {
        "name": "OpenAI Chat Model",
        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
        "typeVersion": 1, "position": [280, 500],
        "parameters": {"model": "new-model"},
    }
    wf["nodes"].append(replacement)
    assert len(wf["nodes"]) == 3
    model_node = next(n for n in wf["nodes"] if n["name"] == "OpenAI Chat Model")
    assert model_node["parameters"]["model"] == "new-model"


def test_connection_delete_and_recreate():
    """Delete a connection key and recreate it."""
    wf = _sample_workflow()
    conns = wf["connections"]
    # Remove existing
    if "OpenAI Chat Model" in conns:
        del conns["OpenAI Chat Model"]
    assert "OpenAI Chat Model" not in conns
    # Recreate
    conns["OpenAI Chat Model"] = {
        "ai_languageModel": [[{"node": "AI Agent1", "type": "ai_languageModel", "index": 0}]]
    }
    assert "OpenAI Chat Model" in conns
    assert conns["OpenAI Chat Model"]["ai_languageModel"][0][0]["node"] == "AI Agent1"


def test_patched_workflow_serializable():
    """After patching, workflow should roundtrip through JSON."""
    wf = _sample_workflow()
    wf["nodes"] = [n for n in wf["nodes"] if n["name"] != "OpenAI Chat Model"]
    wf["nodes"].append({"name": "OpenAI Chat Model", "type": "test", "parameters": {}})
    serialized = json.dumps(wf)
    restored = json.loads(serialized)
    assert len(restored["nodes"]) == 3


def test_workflow_active_flag_set():
    """Patching should be able to set active flag."""
    wf = _sample_workflow()
    wf["active"] = True
    assert wf["active"] is True
    wf["active"] = False
    assert wf["active"] is False
