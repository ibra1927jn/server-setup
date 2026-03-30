"""Tests that directly import and test patch_workflow.py functions."""
import scripts.patch_workflow as pw

# ---------- filter_and_replace_model_node ----------


class TestFilterAndReplace:
    def test_removes_target_adds_replacement(self):
        nodes = [
            {"name": "Trigger"},
            {"name": "OldModel"},
            {"name": "Agent"},
        ]
        new_node = {"name": "NewModel"}
        result = pw.filter_and_replace_model_node(nodes, "OldModel", new_node)
        names = [n["name"] for n in result]
        assert "OldModel" not in names
        assert "NewModel" in names
        assert len(result) == 3

    def test_preserves_other_nodes(self):
        nodes = [{"name": "A", "data": 1}, {"name": "B", "data": 2}]
        result = pw.filter_and_replace_model_node(nodes, "B", {"name": "C"})
        assert result[0] == {"name": "A", "data": 1}

    def test_noop_target_not_found(self):
        nodes = [{"name": "A"}, {"name": "B"}]
        result = pw.filter_and_replace_model_node(nodes, "X", {"name": "Y"})
        assert len(result) == 3  # original 2 + appended replacement

    def test_empty_nodes(self):
        result = pw.filter_and_replace_model_node([], "X", {"name": "Y"})
        assert result == [{"name": "Y"}]

    def test_does_not_mutate_original(self):
        nodes = [{"name": "A"}, {"name": "B"}]
        original_len = len(nodes)
        pw.filter_and_replace_model_node(nodes, "B", {"name": "C"})
        assert len(nodes) == original_len


# ---------- fix_model_connections ----------

class TestFixModelConnections:
    def test_replaces_existing_connection(self):
        conns = {"Model": {"old": "data"}, "Trigger": {"main": []}}
        result = pw.fix_model_connections(conns, "Model", "Agent")
        assert "ai_languageModel" in result["Model"]
        assert result["Model"]["ai_languageModel"][0][0]["node"] == "Agent"

    def test_preserves_other_connections(self):
        conns = {"Model": {}, "Trigger": {"main": [[]]}}
        pw.fix_model_connections(conns, "Model", "Agent")
        assert conns["Trigger"] == {"main": [[]]}

    def test_creates_connection_if_not_exists(self):
        conns = {}
        pw.fix_model_connections(conns, "NewModel", "Agent")
        assert "NewModel" in conns
        assert conns["NewModel"]["ai_languageModel"][0][0]["node"] == "Agent"

    def test_connection_structure(self):
        conns = {}
        pw.fix_model_connections(conns, "M", "A")
        entry = conns["M"]["ai_languageModel"][0][0]
        assert entry == {"node": "A", "type": "ai_languageModel", "index": 0}

    def test_returns_conns(self):
        conns = {"X": {}}
        result = pw.fix_model_connections(conns, "X", "Y")
        assert result is conns


# ---------- build_chat_model_node ----------

class TestBuildChatModelNode:
    def test_default_model(self):
        node = pw.build_chat_model_node()
        assert node["parameters"]["model"] == "z-ai/glm-4.5-air:free"

    def test_custom_model(self):
        node = pw.build_chat_model_node(model="gpt-4")
        assert node["parameters"]["model"] == "gpt-4"

    def test_default_options(self):
        node = pw.build_chat_model_node()
        assert node["parameters"]["options"]["temperature"] == 0.7
        assert node["parameters"]["options"]["maxTokens"] == 500

    def test_node_name_and_type(self):
        node = pw.build_chat_model_node()
        assert node["name"] == "OpenAI Chat Model"
        assert node["type"] == "@n8n/n8n-nodes-langchain.lmChatOpenAi"

    def test_custom_node_id(self):
        node = pw.build_chat_model_node(node_id="my-id")
        assert node["id"] == "my-id"

    def test_custom_cred_id(self):
        node = pw.build_chat_model_node(cred_id="custom-cred")
        assert node["credentials"]["openAiApi"]["id"] == "custom-cred"

    def test_has_position(self):
        node = pw.build_chat_model_node()
        assert node["position"] == [280, 500]

    def test_type_version(self):
        node = pw.build_chat_model_node()
        assert node["typeVersion"] == 1

    def test_credential_name(self):
        node = pw.build_chat_model_node()
        assert node["credentials"]["openAiApi"]["name"] == "OpenRouter Account"
