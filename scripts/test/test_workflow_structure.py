"""Tests for workflow structure validation (fase2_deploy, rebuild_v2 patterns)."""

import json

from deploy.fase2_deploy import gen_id


def _build_daily_briefing(chat_id="123", tg_cred_id="abc", ssh_cred_id="xyz"):
    """Build a Daily Briefing workflow matching the pattern in fase2_deploy.py."""
    return {
        "id": gen_id(),
        "name": "Daily Briefing",
        "nodes": [
            {
                "parameters": {"rule": {"interval": [{"triggerAtHour": 8}]}},
                "id": gen_id(),
                "name": "Cron 8AM",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [250, 300],
            },
            {
                "parameters": {"command": "uptime && df -h /"},
                "id": gen_id(),
                "name": "Check Server",
                "type": "n8n-nodes-base.executeCommand",
                "typeVersion": 1,
                "position": [470, 300],
                "credentials": {"sshPassword": {"id": ssh_cred_id, "name": "SSH"}},
            },
            {
                "parameters": {
                    "chatId": chat_id,
                    "text": "Daily report",
                    "additionalFields": {"parse_mode": "Markdown"},
                },
                "id": gen_id(),
                "name": "Telegram Briefing",
                "type": "n8n-nodes-base.telegram",
                "typeVersion": 1.2,
                "position": [690, 300],
                "credentials": {"telegramApi": {"id": tg_cred_id, "name": "Bot"}},
            },
        ],
        "connections": {
            "Cron 8AM": {"main": [[{"node": "Check Server", "type": "main", "index": 0}]]},
            "Check Server": {"main": [[{"node": "Telegram Briefing", "type": "main", "index": 0}]]},
        },
        "active": True,
        "settings": {"executionOrder": "v1"},
    }


def _build_uptime_monitor(chat_id="123", tg_cred_id="abc"):
    """Build an Uptime Monitor workflow."""
    return {
        "id": gen_id(),
        "name": "Uptime Monitor",
        "nodes": [
            {
                "id": gen_id(),
                "name": "Every 5min",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "parameters": {"rule": {"interval": [{"field": "minutes", "minutesInterval": 5}]}},
                "position": [250, 300],
            },
            {
                "id": gen_id(),
                "name": "Ping Services",
                "type": "n8n-nodes-base.executeCommand",
                "typeVersion": 1,
                "parameters": {"command": "echo test"},
                "position": [470, 300],
            },
            {
                "id": gen_id(),
                "name": "Any Failed?",
                "type": "n8n-nodes-base.if",
                "typeVersion": 2,
                "parameters": {},
                "position": [690, 300],
            },
            {
                "id": gen_id(),
                "name": "Alert Telegram",
                "type": "n8n-nodes-base.telegram",
                "typeVersion": 1.2,
                "parameters": {"chatId": chat_id},
                "position": [910, 200],
                "credentials": {"telegramApi": {"id": tg_cred_id, "name": "Bot"}},
            },
            {
                "id": gen_id(),
                "name": "All OK",
                "type": "n8n-nodes-base.noOp",
                "typeVersion": 1,
                "parameters": {},
                "position": [910, 400],
            },
        ],
        "connections": {
            "Every 5min": {"main": [[{"node": "Ping Services", "type": "main", "index": 0}]]},
            "Ping Services": {"main": [[{"node": "Any Failed?", "type": "main", "index": 0}]]},
            "Any Failed?": {
                "main": [
                    [{"node": "Alert Telegram", "type": "main", "index": 0}],
                    [{"node": "All OK", "type": "main", "index": 0}],
                ]
            },
        },
        "active": True,
    }


# --- gen_id tests ---


def test_gen_id_length():
    assert len(gen_id()) == 16


def test_gen_id_alphanumeric():
    for _ in range(10):
        gid = gen_id()
        assert gid.isalnum()


def test_gen_id_unique():
    ids = {gen_id() for _ in range(50)}
    assert len(ids) == 50  # extremely unlikely collision


# --- Daily Briefing workflow ---


def test_daily_briefing_has_three_nodes():
    wf = _build_daily_briefing()
    assert len(wf["nodes"]) == 3


def test_daily_briefing_node_types():
    wf = _build_daily_briefing()
    types = {n["type"] for n in wf["nodes"]}
    assert "n8n-nodes-base.scheduleTrigger" in types
    assert "n8n-nodes-base.executeCommand" in types
    assert "n8n-nodes-base.telegram" in types


def test_daily_briefing_connections_chain():
    """Nodes should be connected: Cron -> Check Server -> Telegram."""
    wf = _build_daily_briefing()
    conns = wf["connections"]
    assert conns["Cron 8AM"]["main"][0][0]["node"] == "Check Server"
    assert conns["Check Server"]["main"][0][0]["node"] == "Telegram Briefing"


def test_daily_briefing_uses_provided_chat_id():
    wf = _build_daily_briefing(chat_id="999")
    tg = next(n for n in wf["nodes"] if n["type"] == "n8n-nodes-base.telegram")
    assert tg["parameters"]["chatId"] == "999"


def test_daily_briefing_uses_provided_credentials():
    wf = _build_daily_briefing(tg_cred_id="TG1", ssh_cred_id="SSH1")
    tg = next(n for n in wf["nodes"] if n["type"] == "n8n-nodes-base.telegram")
    assert tg["credentials"]["telegramApi"]["id"] == "TG1"
    ssh_node = next(n for n in wf["nodes"] if n["type"] == "n8n-nodes-base.executeCommand")
    assert ssh_node["credentials"]["sshPassword"]["id"] == "SSH1"


def test_daily_briefing_is_active():
    wf = _build_daily_briefing()
    assert wf["active"] is True


def test_daily_briefing_serializable():
    wf = _build_daily_briefing()
    s = json.dumps(wf)
    restored = json.loads(s)
    assert restored["name"] == "Daily Briefing"


# --- Uptime Monitor workflow ---


def test_uptime_monitor_has_five_nodes():
    wf = _build_uptime_monitor()
    assert len(wf["nodes"]) == 5


def test_uptime_monitor_has_if_node():
    wf = _build_uptime_monitor()
    if_nodes = [n for n in wf["nodes"] if n["type"] == "n8n-nodes-base.if"]
    assert len(if_nodes) == 1


def test_uptime_monitor_if_has_two_outputs():
    """The If node should branch to Alert Telegram (true) and All OK (false)."""
    wf = _build_uptime_monitor()
    conns = wf["connections"]
    branches = conns["Any Failed?"]["main"]
    assert len(branches) == 2
    assert branches[0][0]["node"] == "Alert Telegram"
    assert branches[1][0]["node"] == "All OK"


def test_uptime_monitor_trigger_interval():
    wf = _build_uptime_monitor()
    trigger = next(n for n in wf["nodes"] if n["name"] == "Every 5min")
    interval = trigger["parameters"]["rule"]["interval"][0]
    assert interval["minutesInterval"] == 5


def test_uptime_monitor_serializable():
    wf = _build_uptime_monitor()
    s = json.dumps(wf)
    restored = json.loads(s)
    assert restored["name"] == "Uptime Monitor"


def test_all_nodes_have_unique_ids():
    """All node IDs in a workflow must be unique."""
    wf = _build_uptime_monitor()
    ids = [n["id"] for n in wf["nodes"]]
    assert len(ids) == len(set(ids))


def test_connection_targets_reference_existing_nodes():
    """All connection target nodes must exist in the workflow."""
    wf = _build_uptime_monitor()
    node_names = {n["name"] for n in wf["nodes"]}
    for source, conn_data in wf["connections"].items():
        assert source in node_names, f"Source {source} not in nodes"
        for outputs in conn_data.values():
            for branch in outputs:
                for link in branch:
                    assert link["node"] in node_names, f"Target {link['node']} not in nodes"


def test_workflow_id_and_node_ids_differ():
    """Workflow ID should not collide with any node ID."""
    wf = _build_daily_briefing()
    node_ids = {n["id"] for n in wf["nodes"]}
    assert wf["id"] not in node_ids
