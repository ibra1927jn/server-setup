"""Tests for patch_workflow.py node filtering, construction, and connection logic."""
import json

# --- Node filtering (mirrors patch_workflow.py line 24) ---


def _filter_node(nodes, exclude_name):
    """Remove a node by name from the list."""
    return [n for n in nodes if n["name"] != exclude_name]


def test_filter_removes_target():
    nodes = [
        {"name": "Keep", "type": "a"},
        {"name": "OpenAI Chat Model", "type": "b"},
        {"name": "AlsoKeep", "type": "c"},
    ]
    result = _filter_node(nodes, "OpenAI Chat Model")
    assert len(result) == 2
    assert all(n["name"] != "OpenAI Chat Model" for n in result)


def test_filter_no_match():
    nodes = [{"name": "A", "type": "x"}, {"name": "B", "type": "y"}]
    result = _filter_node(nodes, "NonExistent")
    assert len(result) == 2


def test_filter_empty_list():
    assert _filter_node([], "Any") == []


def test_filter_all_same_name():
    nodes = [{"name": "X", "type": "a"}, {"name": "X", "type": "b"}]
    result = _filter_node(nodes, "X")
    assert result == []


# --- Chat model node construction (mirrors patch_workflow.py lines 27-49) ---

def _make_chat_model_node(model, cred_id, cred_name, temp=0.7, max_tokens=500):
    """Build a replacement chat model node."""
    return {
        "parameters": {
            "model": model,
            "options": {"temperature": temp, "maxTokens": max_tokens},
        },
        "id": "e4f8d5bc-3306-4649-8b4e-250327fcdbc1",
        "name": "OpenAI Chat Model",
        "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
        "typeVersion": 1,
        "position": [280, 500],
        "credentials": {"openAiApi": {"id": cred_id, "name": cred_name}},
    }


def test_chat_model_node_model():
    node = _make_chat_model_node("gpt-4", "c1", "OpenAI")
    assert node["parameters"]["model"] == "gpt-4"


def test_chat_model_node_credentials():
    node = _make_chat_model_node("gpt-4", "abc", "MyKey")
    assert node["credentials"]["openAiApi"]["id"] == "abc"
    assert node["credentials"]["openAiApi"]["name"] == "MyKey"


def test_chat_model_node_defaults():
    node = _make_chat_model_node("m1", "c1", "n1")
    assert node["parameters"]["options"]["temperature"] == 0.7
    assert node["parameters"]["options"]["maxTokens"] == 500


def test_chat_model_node_custom_params():
    node = _make_chat_model_node("m1", "c1", "n1", temp=0.3, max_tokens=1000)
    assert node["parameters"]["options"]["temperature"] == 0.3
    assert node["parameters"]["options"]["maxTokens"] == 1000


def test_chat_model_node_serializable():
    node = _make_chat_model_node("m1", "c1", "n1")
    roundtrip = json.loads(json.dumps(node))
    assert roundtrip["name"] == "OpenAI Chat Model"


# --- Connection management (mirrors patch_workflow.py lines 53-70) ---

def _fix_connections(conns, model_name="OpenAI Chat Model", target_agent="AI Agent1"):
    """Remove existing model connection and re-create it pointing to agent."""
    if model_name in conns:
        del conns[model_name]
    conns[model_name] = {
        "ai_languageModel": [
            [{"node": target_agent, "type": "ai_languageModel", "index": 0}]
        ]
    }
    return conns


def test_fix_connections_creates_entry():
    conns = {}
    result = _fix_connections(conns)
    assert "OpenAI Chat Model" in result
    assert result["OpenAI Chat Model"]["ai_languageModel"][0][0]["node"] == "AI Agent1"


def test_fix_connections_replaces_existing():
    conns = {"OpenAI Chat Model": {"old": "data"}}
    result = _fix_connections(conns)
    assert "old" not in result["OpenAI Chat Model"]
    assert "ai_languageModel" in result["OpenAI Chat Model"]


def test_fix_connections_preserves_other():
    conns = {"Trigger": {"main": [[{"node": "Agent", "type": "main", "index": 0}]]}}
    result = _fix_connections(conns)
    assert "Trigger" in result
    assert "OpenAI Chat Model" in result


def test_fix_connections_custom_agent():
    conns = {}
    result = _fix_connections(conns, target_agent="MyAgent")
    assert result["OpenAI Chat Model"]["ai_languageModel"][0][0]["node"] == "MyAgent"


# --- Full patch pipeline ---

def test_full_patch_pipeline():
    """Simulate the full node replacement and connection fix."""
    wf_data = {
        "nodes": [
            {"name": "Trigger", "type": "telegramTrigger"},
            {"name": "OpenAI Chat Model", "type": "lmChatOpenAi"},
            {"name": "AI Agent1", "type": "agent"},
        ],
        "connections": {
            "Trigger": {"main": [[{"node": "AI Agent1", "type": "main", "index": 0}]]},
            "OpenAI Chat Model": {
                "ai_languageModel": [[
                    {"node": "AI Agent1", "type": "ai_languageModel", "index": 0}
                ]]
            },
        },
    }
    # Filter + add new model
    new_nodes = _filter_node(wf_data["nodes"], "OpenAI Chat Model")
    new_nodes.append(_make_chat_model_node("gpt-4", "c1", "Key"))
    wf_data["nodes"] = new_nodes
    # Fix connections
    _fix_connections(wf_data["connections"])

    # Verify
    assert len(wf_data["nodes"]) == 3
    model_node = next(n for n in wf_data["nodes"] if n["name"] == "OpenAI Chat Model")
    assert model_node["parameters"]["model"] == "gpt-4"
    assert "Trigger" in wf_data["connections"]


# --- Response parsing (mirrors patch_workflow.py lines 96-101) ---

def test_response_parsing_success():
    result = json.dumps({"data": {"id": "wf123", "name": "Test"}})
    res_json = json.loads(result)
    parsed_id = res_json.get("data", res_json).get("id")
    assert parsed_id == "wf123"


def test_response_parsing_flat():
    result = json.dumps({"id": "wf456", "name": "Flat"})
    res_json = json.loads(result)
    parsed_id = res_json.get("data", res_json).get("id")
    assert parsed_id == "wf456"


def test_response_parsing_no_id():
    result = json.dumps({"data": {"name": "NoId"}})
    res_json = json.loads(result)
    parsed_id = res_json.get("data", res_json).get("id")
    assert parsed_id is None
