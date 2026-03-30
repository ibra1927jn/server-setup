"""Tests for create_telegram_ai_bot, v2, and v3 workflow builders."""

from create_telegram_ai_bot import build_telegram_ai_workflow as build_v1
from create_telegram_ai_bot_v2 import build_telegram_ai_workflow as build_v2
from create_telegram_ai_bot_v3 import build_telegram_ai_workflow as build_v3


class TestBuildV1:
    def test_has_required_keys(self):
        wf = build_v1()
        assert "name" in wf
        assert "nodes" in wf
        assert "connections" in wf
        assert "settings" in wf

    def test_name(self):
        wf = build_v1()
        assert wf["name"] == "Telegram AI Bot"

    def test_has_three_nodes(self):
        wf = build_v1()
        assert len(wf["nodes"]) == 3

    def test_node_types(self):
        wf = build_v1()
        types = {n["type"] for n in wf["nodes"]}
        assert "n8n-nodes-base.telegramTrigger" in types
        assert "@n8n/n8n-nodes-langchain.agent" in types
        assert "@n8n/n8n-nodes-langchain.lmChatOpenAi" in types

    def test_connections_structure(self):
        wf = build_v1()
        conns = wf["connections"]
        assert "Telegram Trigger" in conns
        assert "GLM-4.5 Air" in conns
        # Trigger connects to AI Agent via main
        assert conns["Telegram Trigger"]["main"][0][0]["node"] == "AI Agent"
        # Model connects to AI Agent via ai_languageModel
        assert conns["GLM-4.5 Air"]["ai_languageModel"][0][0]["node"] == "AI Agent"

    def test_telegram_trigger_has_credentials(self):
        wf = build_v1()
        trigger = [n for n in wf["nodes"] if "Trigger" in n["name"]][0]
        assert "credentials" in trigger
        assert "telegramApi" in trigger["credentials"]

    def test_model_node_has_credentials(self):
        wf = build_v1()
        model = [n for n in wf["nodes"] if "GLM" in n["name"]][0]
        assert "credentials" in model
        assert "openAiApi" in model["credentials"]


class TestBuildV2:
    def test_has_required_keys(self):
        wf = build_v2()
        assert "name" in wf
        assert "nodes" in wf
        assert "connections" in wf

    def test_same_structure_as_v1(self):
        wf = build_v2()
        assert wf["name"] == "Telegram AI Bot"
        assert len(wf["nodes"]) == 3

    def test_execution_order(self):
        wf = build_v2()
        assert wf["settings"]["executionOrder"] == "v1"


class TestBuildV3:
    def test_has_required_keys(self):
        wf = build_v3()
        assert "name" in wf
        assert "nodes" in wf
        assert "connections" in wf
        assert "id" in wf

    def test_generates_unique_ids(self):
        wf1 = build_v3()
        wf2 = build_v3()
        assert wf1["id"] != wf2["id"]

    def test_node_ids_are_unique(self):
        wf = build_v3()
        node_ids = [n["id"] for n in wf["nodes"]]
        assert len(node_ids) == len(set(node_ids))

    def test_active_defaults_false(self):
        wf = build_v3()
        assert wf["active"] is False

    def test_three_nodes(self):
        wf = build_v3()
        assert len(wf["nodes"]) == 3
        types = {n["type"] for n in wf["nodes"]}
        assert "n8n-nodes-base.telegramTrigger" in types
        assert "@n8n/n8n-nodes-langchain.agent" in types

    def test_workflow_id_length(self):
        wf = build_v3()
        assert len(wf["id"]) == 16
