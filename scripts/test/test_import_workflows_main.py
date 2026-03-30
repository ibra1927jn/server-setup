"""Tests for import_workflows_hetzner.py main() with mocked requests."""
from unittest.mock import MagicMock, mock_open, patch

from import_workflows_hetzner import main


def _mock_get_response(workflows=None):
    """Mock GET /api/v1/workflows response."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "data": workflows or [
            {"name": "WF1", "id": "id1", "active": True},
        ]
    }
    return resp


def _mock_post_response(wf_id="new1", status=201):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = {"id": wf_id}
    return resp


def _mock_patch_response(status=200):
    resp = MagicMock()
    resp.status_code = status
    return resp


class TestImportWorkflowsMain:
    @patch("import_workflows_hetzner.os.path.join", side_effect=lambda d, f: f"/flows/{f}")
    @patch("builtins.open", mock_open(read_data='{"name": "Test", "nodes": [], "id": "old"}'))
    @patch("import_workflows_hetzner.requests")
    def test_main_imports_and_activates(self, mock_requests, mock_join, capsys):
        get_resp = _mock_get_response()
        post_resp = _mock_post_response()
        patch_resp = _mock_patch_response()

        mock_requests.get.return_value = get_resp
        mock_requests.post.return_value = post_resp
        mock_requests.patch.return_value = patch_resp

        main()
        out = capsys.readouterr().out
        assert "IMPORT COMPLETE" in out

    @patch("import_workflows_hetzner.os.path.join", side_effect=lambda d, f: f"/flows/{f}")
    @patch("builtins.open", mock_open(read_data='{"name": "WF", "nodes": [{"name": "Start"}]}'))
    @patch("import_workflows_hetzner.requests")
    def test_main_api_error(self, mock_requests, mock_join, capsys):
        """When initial GET fails, prints error."""
        error_resp = MagicMock()
        error_resp.status_code = 401
        error_resp.text = "Unauthorized"
        mock_requests.get.return_value = error_resp

        post_resp = _mock_post_response()
        mock_requests.post.return_value = post_resp
        mock_requests.patch.return_value = _mock_patch_response()

        main()
        out = capsys.readouterr().out
        assert "Error" in out or "Unauthorized" in out

    @patch("import_workflows_hetzner.os.path.join", side_effect=lambda d, f: f"/flows/{f}")
    @patch("builtins.open", mock_open(read_data='{"nodes": []}'))
    @patch("import_workflows_hetzner.requests")
    def test_main_import_failure(self, mock_requests, mock_join, capsys):
        """When POST fails, prints error."""
        mock_requests.get.return_value = _mock_get_response()
        mock_requests.post.return_value = MagicMock(status_code=500)
        mock_requests.patch.return_value = _mock_patch_response()

        main()
        out = capsys.readouterr().out
        assert "Error importing" in out

    @patch("import_workflows_hetzner.os.path.join", side_effect=lambda d, f: f"/flows/{f}")
    @patch("builtins.open", mock_open(read_data='{"name": "WF", "nodes": []}'))
    @patch("import_workflows_hetzner.requests")
    def test_main_activate_failure(self, mock_requests, mock_join, capsys):
        """When PATCH fails, prints Failed."""
        mock_requests.get.return_value = _mock_get_response()
        mock_requests.post.return_value = _mock_post_response()
        mock_requests.patch.return_value = _mock_patch_response(status=500)

        main()
        out = capsys.readouterr().out
        assert "Failed" in out

    @patch("import_workflows_hetzner.os.path.join", side_effect=lambda d, f: f"/flows/{f}")
    @patch("builtins.open", mock_open(read_data='{"name": "WF", "nodes": [], "id": "x"}'))
    @patch("import_workflows_hetzner.requests")
    def test_main_final_listing(self, mock_requests, mock_join, capsys):
        """Final listing shows all workflows."""
        final_wfs = [
            {"name": "WF1", "id": "1", "active": True},
            {"name": "WF2", "id": "2", "active": False},
        ]
        mock_requests.get.return_value = _mock_get_response(final_wfs)
        mock_requests.post.return_value = _mock_post_response()
        mock_requests.patch.return_value = _mock_patch_response()

        main()
        out = capsys.readouterr().out
        assert "Total: 2 workflows" in out
