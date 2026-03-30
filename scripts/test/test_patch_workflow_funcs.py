"""Tests for patch_workflow.py extracted functions"""
from patch_workflow import (
    build_chat_model_node,
    filter_and_replace_model_node,
    fix_model_connections,
)


class TestFilterAndReplaceModelNode:
    def test_replaces_existing_node(self):
        nodes = [
            {"name": "Trigger", "type": "trigger"},
            {"name": "OpenAI Chat Model", "type": "old-model"},
            {"name": "Agent", "type": "agent"},
        ]
        new_node = {"name": "OpenAI Chat Model", "type": "new-model"}
        result = filter_and_replace_model_node(nodes, "OpenAI Chat Model", new_node)
        assert len(result) == 3
        names = [n["name"] for n in result]
        assert names.count("OpenAI Chat Model") == 1
        model = next(n for n in result if n["name"] == "OpenAI Chat Model")
        assert model["type"] == "new-model"

    def test_adds_when_not_present(self):
        nodes = [{"name": "Trigger", "type": "trigger"}]
        new_node = {"name": "Model", "type": "model"}
        result = filter_and_replace_model_node(nodes, "Model", new_node)
        assert len(result) == 2

    def test_empty_nodes(self):
        new_node = {"name": "Model", "type": "model"}
        result = filter_and_replace_model_node([], "Model", new_node)
        assert result == [new_node]

    def test_does_not_mutate_original(self):
        nodes = [{"name": "A", "type": "a"}, {"name": "B", "type": "b"}]
        original_len = len(nodes)
        filter_and_replace_model_node(nodes, "A", {"name": "A", "type": "new"})
        assert len(nodes) == original_len

    def test_preserves_other_nodes(self):
        nodes = [
            {"name": "Keep1", "type": "t1"},
            {"name": "Remove", "type": "old"},
            {"name": "Keep2", "type": "t2"},
        ]
        result = filter_and_replace_model_node(
            nodes, "Remove", {"name": "Remove", "type": "new"}
        )
        kept = [n for n in result if n["name"].startswith("Keep")]
        assert len(kept) == 2


class TestFixModelConnections:
    def test_creates_connection(self):
        conns = {}
        result = fix_model_connections(conns, "Model", "Agent1")
        assert "Model" in result
        link = result["Model"]["ai_languageModel"][0][0]
        assert link["node"] == "Agent1"
        assert link["type"] == "ai_languageModel"
        assert link["index"] == 0

    def test_replaces_existing_connection(self):
        conns = {"Model": {"old": "data"}, "Other": {"keep": True}}
        result = fix_model_connections(conns, "Model", "Agent1")
        assert "ai_languageModel" in result["Model"]
        assert "old" not in result["Model"]
        assert result["Other"] == {"keep": True}

    def test_mutates_in_place(self):
        conns = {}
        result = fix_model_connections(conns, "M", "A")
        assert result is conns

    def test_different_agent_name(self):
        conns = {}
        fix_model_connections(conns, "Chat", "MyCustomAgent")
        assert conns["Chat"]["ai_languageModel"][0][0]["node"] == "MyCustomAgent"


class TestBuildChatModelNode:
    def test_default_values(self):
        node = build_chat_model_node()
        assert node["name"] == "OpenAI Chat Model"
        assert node["parameters"]["model"] == "z-ai/glm-4.5-air:free"
        assert node["typeVersion"] == 1
        assert node["credentials"]["openAiApi"]["id"] == "D98S1Z0HkO9oWJ54"

    def test_custom_model(self):
        node = build_chat_model_node(model="gpt-4")
        assert node["parameters"]["model"] == "gpt-4"

    def test_custom_cred_id(self):
        node = build_chat_model_node(cred_id="custom123")
        assert node["credentials"]["openAiApi"]["id"] == "custom123"

    def test_custom_node_id(self):
        node = build_chat_model_node(node_id="my-id")
        assert node["id"] == "my-id"

    def test_has_required_fields(self):
        node = build_chat_model_node()
        assert "parameters" in node
        assert "id" in node
        assert "name" in node
        assert "type" in node
        assert "position" in node
        assert "credentials" in node
