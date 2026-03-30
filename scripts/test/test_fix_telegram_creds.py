"""Tests for pure functions extracted from fix_telegram_creds.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fix.fix_telegram_creds import index_credentials_by_type, patch_workflow_credentials


class TestIndexCredentialsByType:
    def test_empty_list(self):
        assert index_credentials_by_type([]) == {}

    def test_single_credential(self):
        creds = [{"id": "1", "name": "My Telegram", "type": "telegramApi"}]
        result = index_credentials_by_type(creds)
        assert result == {"telegramApi": {"id": "1", "name": "My Telegram"}}

    def test_multiple_credentials(self):
        creds = [
            {"id": "1", "name": "Telegram", "type": "telegramApi"},
            {"id": "2", "name": "SSH Key", "type": "sshPassword"},
            {"id": "3", "name": "OpenAI", "type": "openAiApi"},
        ]
        result = index_credentials_by_type(creds)
        assert len(result) == 3
        assert result["telegramApi"]["id"] == "1"
        assert result["sshPassword"]["id"] == "2"
        assert result["openAiApi"]["id"] == "3"

    def test_duplicate_type_last_wins(self):
        creds = [
            {"id": "1", "name": "Old", "type": "telegramApi"},
            {"id": "2", "name": "New", "type": "telegramApi"},
        ]
        result = index_credentials_by_type(creds)
        assert result["telegramApi"]["id"] == "2"

    def test_missing_fields_default_empty(self):
        creds = [{"type": "telegramApi"}]
        result = index_credentials_by_type(creds)
        assert result["telegramApi"] == {"id": "", "name": ""}

    def test_missing_type_uses_empty_key(self):
        creds = [{"id": "1", "name": "Orphan"}]
        result = index_credentials_by_type(creds)
        assert "" in result


class TestPatchWorkflowCredentials:
    def _make_wf(self, nodes):
        return {"name": "Test", "nodes": nodes}

    def test_no_nodes(self):
        wf = self._make_wf([])
        assert patch_workflow_credentials(wf, {"id": "1", "name": "T"}, {}) is False

    def test_non_matching_node_unchanged(self):
        wf = self._make_wf([
            {"name": "Cron", "type": "n8n-nodes-base.scheduleTrigger", "parameters": {}},
        ])
        assert patch_workflow_credentials(wf, {"id": "1", "name": "T"}, {}) is False

    def test_telegram_node_patched(self):
        wf = self._make_wf([
            {
                "name": "Send Msg",
                "type": "n8n-nodes-base.telegram",
                "credentials": {"telegramApi": {"id": "old", "name": "Old"}},
            },
        ])
        result = patch_workflow_credentials(
            wf, {"id": "99", "name": "Real Telegram"}, {}
        )
        assert result is True
        assert wf["nodes"][0]["credentials"]["telegramApi"]["id"] == "99"
        assert wf["nodes"][0]["credentials"]["telegramApi"]["name"] == "Real Telegram"

    def test_ssh_node_patched(self):
        wf = self._make_wf([
            {
                "name": "Run Cmd",
                "type": "n8n-nodes-base.ssh",
                "credentials": {"sshPassword": {"id": "old", "name": "Old"}},
            },
        ])
        result = patch_workflow_credentials(
            wf, {"id": "1", "name": "T"}, {"id": "55", "name": "Real SSH"}
        )
        assert result is True
        assert wf["nodes"][0]["credentials"]["sshPassword"]["id"] == "55"

    def test_ssh_node_skipped_when_no_ssh_cred_id(self):
        wf = self._make_wf([
            {
                "name": "Run Cmd",
                "type": "n8n-nodes-base.ssh",
                "credentials": {"sshPassword": {"id": "old", "name": "Old"}},
            },
        ])
        result = patch_workflow_credentials(
            wf, {"id": "1", "name": "T"}, {}
        )
        assert result is False
        assert wf["nodes"][0]["credentials"]["sshPassword"]["id"] == "old"

    def test_mixed_nodes(self):
        wf = self._make_wf([
            {"name": "Cron", "type": "n8n-nodes-base.scheduleTrigger", "parameters": {}},
            {
                "name": "Send",
                "type": "n8n-nodes-base.telegram",
                "credentials": {"telegramApi": {"id": "x", "name": "x"}},
            },
            {
                "name": "SSH",
                "type": "n8n-nodes-base.ssh",
                "credentials": {"sshPassword": {"id": "x", "name": "x"}},
            },
        ])
        result = patch_workflow_credentials(
            wf,
            {"id": "T1", "name": "Telegram"},
            {"id": "S1", "name": "SSH"},
        )
        assert result is True
        assert wf["nodes"][1]["credentials"]["telegramApi"]["id"] == "T1"
        assert wf["nodes"][2]["credentials"]["sshPassword"]["id"] == "S1"

    def test_empty_workflow_no_nodes_key(self):
        wf = {"name": "Empty"}
        assert patch_workflow_credentials(wf, {"id": "1", "name": "T"}, {}) is False
