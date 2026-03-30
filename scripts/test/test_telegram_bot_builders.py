"""Tests for build_telegram_ai_workflow() in all three bot creation scripts."""
import json

from create_telegram_ai_bot import (
    build_telegram_ai_workflow as build_v1,
)
from create_telegram_ai_bot_v2 import (
    build_telegram_ai_workflow as build_v2,
)
from create_telegram_ai_bot_v3 import (
    build_telegram_ai_workflow as build_v3,
)


class TestBuildV1:
    def test_returns_dict(self):
        wf = build_v1()
        assert isinstance(wf, dict)

    def test_has_name(self):
        assert build_v1()["name"] == "Telegram AI Bot"

    def test_has_three_nodes(self):
        assert len(build_v1()["nodes"]) == 3

    def test_node_types(self):
        types = {n["type"] for n in build_v1()["nodes"]}
        assert "n8n-nodes-base.telegramTrigger" in types
        assert "@n8n/n8n-nodes-langchain.agent" in types
        assert "@n8n/n8n-nodes-langchain.lmChatOpenAi" in types

    def test_connections_exist(self):
        conns = build_v1()["connections"]
        assert "Telegram Trigger" in conns
        assert "GLM-4.5 Air" in conns

    def test_trigger_connects_to_agent(self):
        conns = build_v1()["connections"]
        target = conns["Telegram Trigger"]["main"][0][0]["node"]
        assert target == "AI Agent"

    def test_model_connects_to_agent(self):
        conns = build_v1()["connections"]
        target = conns["GLM-4.5 Air"]["ai_languageModel"][0][0]["node"]
        assert target == "AI Agent"

    def test_execution_order(self):
        assert build_v1()["settings"]["executionOrder"] == "v1"

    def test_json_serializable(self):
        serialized = json.dumps(build_v1())
        restored = json.loads(serialized)
        assert restored["name"] == "Telegram AI Bot"


class TestBuildV2:
    def test_returns_dict(self):
        assert isinstance(build_v2(), dict)

    def test_has_name(self):
        assert build_v2()["name"] == "Telegram AI Bot"

    def test_has_three_nodes(self):
        assert len(build_v2()["nodes"]) == 3

    def test_connections(self):
        conns = build_v2()["connections"]
        assert "Telegram Trigger" in conns
        assert "GLM-4.5 Air" in conns

    def test_json_serializable(self):
        json.dumps(build_v2())  # should not raise


class TestBuildV3:
    def test_returns_dict(self):
        assert isinstance(build_v3(), dict)

    def test_has_workflow_id(self):
        wf = build_v3()
        assert "id" in wf
        assert len(wf["id"]) == 16

    def test_unique_ids_per_call(self):
        id1 = build_v3()["id"]
        id2 = build_v3()["id"]
        assert id1 != id2

    def test_has_active_false(self):
        assert build_v3()["active"] is False

    def test_has_three_nodes(self):
        assert len(build_v3()["nodes"]) == 3

    def test_node_ids_are_unique(self):
        node_ids = [n["id"] for n in build_v3()["nodes"]]
        assert len(set(node_ids)) == 3

    def test_connections(self):
        conns = build_v3()["connections"]
        assert "Telegram Trigger" in conns
        assert "GLM-4.5 Air" in conns

    def test_json_serializable(self):
        serialized = json.dumps(build_v3())
        restored = json.loads(serialized)
        assert restored["name"] == "Telegram AI Bot"
        assert restored["active"] is False
