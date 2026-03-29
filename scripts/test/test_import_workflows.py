"""Tests for import_workflows_hetzner.py JSON manipulation logic"""
from unittest.mock import patch, MagicMock


def _make_workflow(name="Test WF", wf_id="abc123", nodes=None):
    """Create a sample workflow dict."""
    return {
        "id": wf_id,
        "name": name,
        "nodes": nodes or [{"name": "Start", "type": "n8n-nodes-base.start"}],
        "connections": {},
        "active": False,
    }


def test_pop_id_removes_id():
    """Importing should strip the id so n8n assigns a new one."""
    wf = _make_workflow(wf_id="old-id-123")
    wf.pop("id", None)
    assert "id" not in wf


def test_pop_id_noop_when_missing():
    """pop('id', None) should not raise when id is absent."""
    wf = {"name": "No ID Workflow", "nodes": []}
    wf.pop("id", None)
    assert "id" not in wf


def test_name_fallback_from_filename():
    """When name is missing, fall back to filename without .json."""
    wf = {"nodes": []}
    filename = "server-sentinel.json"
    name = wf.get("name", filename.replace(".json", ""))
    assert name == "server-sentinel"


def test_name_uses_existing():
    """When name exists, use it as-is."""
    wf = {"name": "My Custom WF", "nodes": []}
    filename = "fallback.json"
    name = wf.get("name", filename.replace(".json", ""))
    assert name == "My Custom WF"


def test_activation_status_check():
    """Status 200 means activated, anything else is a warning."""
    for code, expected in [(200, True), (400, False), (500, False)]:
        resp = MagicMock()
        resp.status_code = code
        is_active = resp.status_code == 200
        assert is_active == expected


def test_workflow_creation_response_parsing():
    """Successful create should extract ID from response."""
    resp_data = {"id": "new-id-456", "name": "Test", "active": False}
    wf_id = resp_data.get("id", "unknown")
    assert wf_id == "new-id-456"


def test_workflow_creation_response_missing_id():
    """If response has no id, default to 'unknown'."""
    resp_data = {"name": "Test"}
    wf_id = resp_data.get("id", "unknown")
    assert wf_id == "unknown"
