"""Tests for import_workflows_hetzner.py pure functions"""
from unittest.mock import MagicMock, patch

from import_workflows_hetzner import (
    activate_workflow,
    import_workflow,
    prepare_workflow,
)


class TestPrepareWorkflow:
    def test_removes_id(self):
        data = {"id": "old123", "name": "Test", "nodes": []}
        result = prepare_workflow(data, "test.json")
        assert "id" not in result

    def test_preserves_existing_name(self):
        data = {"name": "My Workflow", "nodes": []}
        result = prepare_workflow(data, "fallback.json")
        assert result["name"] == "My Workflow"

    def test_sets_name_from_filename_when_missing(self):
        data = {"nodes": []}
        result = prepare_workflow(data, "server-sentinel.json")
        assert result["name"] == "server-sentinel"

    def test_sets_name_from_filename_when_empty(self):
        data = {"name": "", "nodes": []}
        result = prepare_workflow(data, "my-flow.json")
        assert result["name"] == "my-flow"

    def test_preserves_nodes(self):
        nodes = [{"name": "Trigger", "type": "start"}]
        data = {"id": "x", "name": "Test", "nodes": nodes}
        result = prepare_workflow(data, "t.json")
        assert result["nodes"] == nodes

    def test_mutates_in_place(self):
        data = {"id": "x", "name": "Test"}
        result = prepare_workflow(data, "t.json")
        assert result is data


class TestImportWorkflow:
    def test_successful_import(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"id": "new123"}

        with patch("import_workflows_hetzner.requests.post", return_value=mock_resp):
            result = import_workflow("http://n8n:5678", {}, {"name": "Test"})

        assert result == ("Test", "new123")

    def test_import_200(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"id": "abc"}

        with patch("import_workflows_hetzner.requests.post", return_value=mock_resp):
            result = import_workflow("http://n8n:5678", {}, {"name": "WF"})

        assert result == ("WF", "abc")

    def test_import_failure_returns_none(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 500

        with patch("import_workflows_hetzner.requests.post", return_value=mock_resp):
            result = import_workflow("http://n8n:5678", {}, {"name": "Bad"})

        assert result is None

    def test_missing_id_in_response(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {}

        with patch("import_workflows_hetzner.requests.post", return_value=mock_resp):
            result = import_workflow("http://n8n:5678", {}, {"name": "X"})

        assert result == ("X", "unknown")


class TestActivateWorkflow:
    def test_activate_success(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch("import_workflows_hetzner.requests.patch", return_value=mock_resp):
            assert activate_workflow("http://n8n:5678", {}, "abc") is True

    def test_activate_failure(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 404

        with patch("import_workflows_hetzner.requests.patch", return_value=mock_resp):
            assert activate_workflow("http://n8n:5678", {}, "abc") is False
