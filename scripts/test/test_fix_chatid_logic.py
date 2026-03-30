"""Tests for chat ID replacement logic used in fix_chatid.py"""
import json

WRONG_CHAT_ID = "6915862027"
REAL_CHAT_ID = "5822131920"


def _make_workflow(chat_id, name="Test Workflow"):
    """Create a workflow with a Telegram node using the given chatId."""
    return {
        "name": name,
        "id": "abc123",
        "nodes": [
            {
                "name": "Cron",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "parameters": {"rule": {"interval": [{"triggerAtHour": 8}]}},
            },
            {
                "name": "Send Telegram",
                "type": "n8n-nodes-base.telegram",
                "typeVersion": 1.2,
                "parameters": {
                    "chatId": chat_id,
                    "text": f"Hello from chat {chat_id}",
                    "additionalFields": {"parse_mode": "Markdown"},
                },
            },
        ],
        "connections": {
            "Cron": {"main": [[{"node": "Send Telegram", "type": "main", "index": 0}]]}
        },
    }


def _fix_chatids(wf, wrong_id, real_id):
    """Replicate the chat ID fix logic from fix_chatid.py."""
    changed = False
    for node in wf.get("nodes", []):
        params = node.get("parameters", {})
        if "chatId" in params and params["chatId"] == wrong_id:
            params["chatId"] = real_id
            changed = True
        text = params.get("text", "")
        if wrong_id in str(text):
            params["text"] = str(text).replace(wrong_id, real_id)
            changed = True
    return changed


def test_fix_wrong_chatid():
    """Should replace wrong chatId with the correct one."""
    wf = _make_workflow(WRONG_CHAT_ID)
    changed = _fix_chatids(wf, WRONG_CHAT_ID, REAL_CHAT_ID)
    assert changed is True
    tg_node = [n for n in wf["nodes"] if n["name"] == "Send Telegram"][0]
    assert tg_node["parameters"]["chatId"] == REAL_CHAT_ID


def test_fix_chatid_in_text():
    """Should also replace chatId references in text fields."""
    wf = _make_workflow(WRONG_CHAT_ID)
    changed = _fix_chatids(wf, WRONG_CHAT_ID, REAL_CHAT_ID)
    assert changed is True
    tg_node = [n for n in wf["nodes"] if n["name"] == "Send Telegram"][0]
    assert WRONG_CHAT_ID not in tg_node["parameters"]["text"]
    assert REAL_CHAT_ID in tg_node["parameters"]["text"]


def test_no_change_when_already_correct():
    """Should not flag changes when chatId is already correct."""
    wf = _make_workflow(REAL_CHAT_ID)
    # Text field also uses REAL_CHAT_ID, so won't match wrong
    wf["nodes"][1]["parameters"]["text"] = "Hello world"
    changed = _fix_chatids(wf, WRONG_CHAT_ID, REAL_CHAT_ID)
    assert changed is False


def test_fix_multiple_telegram_nodes():
    """Should fix chatId in all Telegram nodes."""
    wf = _make_workflow(WRONG_CHAT_ID)
    wf["nodes"].append({
        "name": "Alert Telegram",
        "type": "n8n-nodes-base.telegram",
        "typeVersion": 1.2,
        "parameters": {"chatId": WRONG_CHAT_ID, "text": "Alert!"},
    })
    changed = _fix_chatids(wf, WRONG_CHAT_ID, REAL_CHAT_ID)
    assert changed is True
    for node in wf["nodes"]:
        if node["type"] == "n8n-nodes-base.telegram":
            assert node["parameters"]["chatId"] == REAL_CHAT_ID


def test_fix_does_not_touch_non_telegram_nodes():
    """Non-telegram nodes should not be modified."""
    wf = _make_workflow(WRONG_CHAT_ID)
    cron_params_before = json.dumps(wf["nodes"][0]["parameters"])
    _fix_chatids(wf, WRONG_CHAT_ID, REAL_CHAT_ID)
    cron_params_after = json.dumps(wf["nodes"][0]["parameters"])
    assert cron_params_before == cron_params_after


def test_fix_across_multiple_workflows():
    """Should work across a list of workflows."""
    workflows = [
        _make_workflow(WRONG_CHAT_ID, "WF1"),
        _make_workflow(REAL_CHAT_ID, "WF2"),  # already correct
        _make_workflow(WRONG_CHAT_ID, "WF3"),
    ]
    # Clear text refs in WF2 so it's truly unchanged
    workflows[1]["nodes"][1]["parameters"]["text"] = "Hello world"
    fixed_count = 0
    for wf in workflows:
        if _fix_chatids(wf, WRONG_CHAT_ID, REAL_CHAT_ID):
            fixed_count += 1
    assert fixed_count == 2


def test_empty_workflow_no_crash():
    """Workflow with no nodes should not crash."""
    wf = {"name": "Empty", "nodes": []}
    changed = _fix_chatids(wf, WRONG_CHAT_ID, REAL_CHAT_ID)
    assert changed is False


def test_node_without_parameters():
    """Node missing parameters key should not crash."""
    wf = {"name": "Bare", "nodes": [{"name": "NoParams", "type": "test"}]}
    changed = _fix_chatids(wf, WRONG_CHAT_ID, REAL_CHAT_ID)
    assert changed is False
