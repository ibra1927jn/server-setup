"""Tests for build_telegram_ai_workflow() across all three bot script versions."""

import scripts.create_telegram_ai_bot as bot_v1
import scripts.create_telegram_ai_bot_v2 as bot_v2
import scripts.create_telegram_ai_bot_v3 as bot_v3

# ---------- v1: create_telegram_ai_bot ----------


class TestBotV1:
    def test_workflow_name(self):
        wf = bot_v1.build_telegram_ai_workflow()
        assert wf["name"] == "Telegram AI Bot"

    def test_has_three_nodes(self):
        wf = bot_v1.build_telegram_ai_workflow()
        assert len(wf["nodes"]) == 3

    def test_node_types(self):
        wf = bot_v1.build_telegram_ai_workflow()
        types = {n["type"] for n in wf["nodes"]}
        assert "n8n-nodes-base.telegramTrigger" in types
        assert "@n8n/n8n-nodes-langchain.agent" in types
        assert "@n8n/n8n-nodes-langchain.lmChatOpenAi" in types

    def test_node_names(self):
        wf = bot_v1.build_telegram_ai_workflow()
        names = {n["name"] for n in wf["nodes"]}
        assert names == {"Telegram Trigger", "AI Agent", "GLM-4.5 Air"}

    def test_connections_trigger_to_agent(self):
        wf = bot_v1.build_telegram_ai_workflow()
        target = wf["connections"]["Telegram Trigger"]["main"][0][0]
        assert target["node"] == "AI Agent"
        assert target["type"] == "main"

    def test_connections_model_to_agent(self):
        wf = bot_v1.build_telegram_ai_workflow()
        target = wf["connections"]["GLM-4.5 Air"]["ai_languageModel"][0][0]
        assert target["node"] == "AI Agent"

    def test_telegram_trigger_has_credentials(self):
        wf = bot_v1.build_telegram_ai_workflow()
        trigger = next(n for n in wf["nodes"] if n["name"] == "Telegram Trigger")
        assert "telegramApi" in trigger["credentials"]

    def test_model_has_credentials(self):
        wf = bot_v1.build_telegram_ai_workflow()
        model = next(n for n in wf["nodes"] if n["name"] == "GLM-4.5 Air")
        assert "openAiApi" in model["credentials"]

    def test_settings(self):
        wf = bot_v1.build_telegram_ai_workflow()
        assert wf["settings"]["executionOrder"] == "v1"

    def test_node_positions_are_lists(self):
        wf = bot_v1.build_telegram_ai_workflow()
        for node in wf["nodes"]:
            assert isinstance(node["position"], list)
            assert len(node["position"]) == 2


# ---------- v2: create_telegram_ai_bot_v2 ----------


class TestBotV2:
    def test_workflow_name(self):
        wf = bot_v2.build_telegram_ai_workflow()
        assert wf["name"] == "Telegram AI Bot"

    def test_has_three_nodes(self):
        wf = bot_v2.build_telegram_ai_workflow()
        assert len(wf["nodes"]) == 3

    def test_same_node_types_as_v1(self):
        wf_v1 = bot_v1.build_telegram_ai_workflow()
        wf_v2 = bot_v2.build_telegram_ai_workflow()
        types_v1 = {n["type"] for n in wf_v1["nodes"]}
        types_v2 = {n["type"] for n in wf_v2["nodes"]}
        assert types_v1 == types_v2

    def test_connections_structure(self):
        wf = bot_v2.build_telegram_ai_workflow()
        assert "Telegram Trigger" in wf["connections"]
        assert "GLM-4.5 Air" in wf["connections"]

    def test_agent_has_system_message(self):
        wf = bot_v2.build_telegram_ai_workflow()
        agent = next(n for n in wf["nodes"] if n["name"] == "AI Agent")
        msg = agent["parameters"]["options"]["systemMessage"]
        assert "AgenticOS" in msg


# ---------- v3: create_telegram_ai_bot_v3 (UUID-based IDs) ----------


class TestBotV3:
    def test_workflow_has_hex_id(self):
        wf = bot_v3.build_telegram_ai_workflow()
        assert len(wf["id"]) == 16
        assert wf["id"].isalnum()

    def test_node_ids_are_unique(self):
        wf = bot_v3.build_telegram_ai_workflow()
        ids = [n["id"] for n in wf["nodes"]]
        assert len(ids) == len(set(ids))

    def test_node_ids_are_short_hex(self):
        wf = bot_v3.build_telegram_ai_workflow()
        for node in wf["nodes"]:
            assert len(node["id"]) == 8
            assert node["id"].isalnum()

    def test_workflow_starts_inactive(self):
        wf = bot_v3.build_telegram_ai_workflow()
        assert wf["active"] is False

    def test_two_calls_produce_different_ids(self):
        wf1 = bot_v3.build_telegram_ai_workflow()
        wf2 = bot_v3.build_telegram_ai_workflow()
        assert wf1["id"] != wf2["id"]

    def test_has_three_nodes(self):
        wf = bot_v3.build_telegram_ai_workflow()
        assert len(wf["nodes"]) == 3

    def test_connections_structure(self):
        wf = bot_v3.build_telegram_ai_workflow()
        assert "Telegram Trigger" in wf["connections"]
        assert "GLM-4.5 Air" in wf["connections"]

    def test_model_options(self):
        wf = bot_v3.build_telegram_ai_workflow()
        model = next(n for n in wf["nodes"] if n["name"] == "GLM-4.5 Air")
        assert model["parameters"]["options"]["maxTokens"] == 500
        assert model["parameters"]["options"]["temperature"] == 0.7
