"""Tests for workflow export/analysis logic (from export_analyze_workflow.py patterns)."""


def _sample_export_response():
    """Simulate n8n REST API workflow export response."""
    return {
        "data": {
            "id": "WiTcSI66bHwdSgkd",
            "name": "AI Agent Base",
            "nodes": [
                {"name": "Telegram Trigger", "type": "n8n-nodes-base.telegramTrigger", "typeVersion": 1},
                {"name": "AI Agent1", "type": "@n8n/n8n-nodes-langchain.agent", "typeVersion": 1.6},
                {
                    "name": "OpenAI Chat Model",
                    "type": "@n8n/n8n-nodes-langchain.lmChatOpenAi",
                    "typeVersion": 1,
                    "credentials": {"openAiApi": {"id": "cred1", "name": "OpenAI"}},
                },
            ],
            "connections": {
                "Telegram Trigger": {"main": [[{"node": "AI Agent1", "type": "main", "index": 0}]]},
                "OpenAI Chat Model": {"ai_languageModel": [[{"node": "AI Agent1", "type": "ai_languageModel", "index": 0}]]},
            },
        }
    }


def _extract_workflow_data(response):
    """Replicate the extraction logic from export_analyze_workflow.py."""
    return response.get("data", response)


def _list_nodes(wf_data):
    """Extract node info list."""
    return [{"name": n["name"], "type": n["type"], "version": n.get("typeVersion")} for n in wf_data.get("nodes", [])]


def _get_connections(wf_data):
    """Get connection summary."""
    result = {}
    for source, conn_data in wf_data.get("connections", {}).items():
        targets = []
        for conn_type, branches in conn_data.items():
            for branch in branches:
                targets.extend({"node": link["node"], "type": conn_type} for link in branch)
        result[source] = targets
    return result


# --- extract workflow data ---


def test_extract_from_data_wrapper():
    resp = _sample_export_response()
    wf = _extract_workflow_data(resp)
    assert wf["name"] == "AI Agent Base"
    assert "nodes" in wf


def test_extract_from_flat_response():
    """When response has no 'data' key, use it directly."""
    flat = {"name": "Direct", "nodes": [], "connections": {}}
    wf = _extract_workflow_data(flat)
    assert wf["name"] == "Direct"


def test_extract_preserves_all_fields():
    resp = _sample_export_response()
    wf = _extract_workflow_data(resp)
    assert "id" in wf
    assert "connections" in wf


# --- list nodes ---


def test_list_nodes_count():
    resp = _sample_export_response()
    wf = _extract_workflow_data(resp)
    nodes = _list_nodes(wf)
    assert len(nodes) == 3


def test_list_nodes_fields():
    resp = _sample_export_response()
    wf = _extract_workflow_data(resp)
    nodes = _list_nodes(wf)
    agent = next(n for n in nodes if n["name"] == "AI Agent1")
    assert agent["type"] == "@n8n/n8n-nodes-langchain.agent"
    assert agent["version"] == 1.6


def test_list_nodes_empty_workflow():
    wf = {"name": "Empty", "nodes": []}
    nodes = _list_nodes(wf)
    assert nodes == []


def test_list_nodes_missing_version():
    wf = {"nodes": [{"name": "X", "type": "test"}]}
    nodes = _list_nodes(wf)
    assert nodes[0]["version"] is None


# --- connections ---


def test_get_connections_main():
    resp = _sample_export_response()
    wf = _extract_workflow_data(resp)
    conns = _get_connections(wf)
    assert "Telegram Trigger" in conns
    assert conns["Telegram Trigger"][0]["node"] == "AI Agent1"


def test_get_connections_ai_language_model():
    resp = _sample_export_response()
    wf = _extract_workflow_data(resp)
    conns = _get_connections(wf)
    assert "OpenAI Chat Model" in conns
    link = conns["OpenAI Chat Model"][0]
    assert link["type"] == "ai_languageModel"
    assert link["node"] == "AI Agent1"


def test_get_connections_empty():
    wf = {"connections": {}}
    conns = _get_connections(wf)
    assert conns == {}


def test_credential_extraction_from_nodes():
    """Extract credential IDs from workflow nodes."""
    resp = _sample_export_response()
    wf = _extract_workflow_data(resp)
    # Pattern used in rebuild_v2.py: extract cred IDs from exported workflows
    creds = []
    for node in wf.get("nodes", []):
        for cred_type, cred_info in node.get("credentials", {}).items():
            creds.append({"type": cred_type, "id": cred_info.get("id"), "name": cred_info.get("name")})
    assert creds == [{"type": "openAiApi", "id": "cred1", "name": "OpenAI"}]


def test_workflow_id_extraction():
    """Import response should provide workflow ID."""
    # Simulates n8n POST /api/v1/workflows response
    import_resp = {"id": "newId123", "name": "Imported WF", "active": False}
    wf_id = import_resp.get("id", "unknown")
    assert wf_id == "newId123"


def test_workflow_name_fallback():
    """Name should fallback from filename when not in data."""
    filename = "server-sentinel.json"
    data = {"nodes": []}
    name = data.get("name", filename.replace(".json", ""))
    assert name == "server-sentinel"


def test_workflow_name_from_data():
    data = {"name": "My Workflow", "nodes": []}
    name = data.get("name", "fallback")
    assert name == "My Workflow"
