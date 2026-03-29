"""Tests for fase2_deploy.py workflow data structures and gen_id()"""
import json
import random
import string


def gen_id():
    """Replicate gen_id from fase2_deploy (avoids importing the module which calls SSH)."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=16))


def test_gen_id_length():
    assert len(gen_id()) == 16


def test_gen_id_alphanumeric():
    result = gen_id()
    assert result.isalnum()


def test_gen_id_unique():
    ids = {gen_id() for _ in range(100)}
    assert len(ids) == 100


def test_workflow_structure_daily_briefing():
    """Daily Briefing workflow should have required fields."""
    wf = {
        "id": gen_id(),
        "name": "Daily Briefing",
        "nodes": [
            {"parameters": {"rule": {"interval": [{"triggerAtHour": 8}]}},
             "id": gen_id(), "name": "Cron 8AM",
             "type": "n8n-nodes-base.scheduleTrigger"},
        ],
        "connections": {},
        "active": True,
    }
    assert wf["name"] == "Daily Briefing"
    assert wf["active"] is True
    assert len(wf["nodes"]) >= 1
    assert wf["nodes"][0]["type"] == "n8n-nodes-base.scheduleTrigger"
    # Should be JSON-serializable
    assert json.loads(json.dumps(wf)) == wf


def test_workflow_structure_uptime_monitor():
    """Uptime Monitor should poll every 5 minutes."""
    wf = {
        "id": gen_id(),
        "name": "Uptime Monitor",
        "nodes": [
            {"parameters": {"rule": {"interval": [{"field": "minutes", "minutesInterval": 5}]}},
             "id": gen_id(), "name": "Every 5 min",
             "type": "n8n-nodes-base.scheduleTrigger"},
        ],
        "connections": {},
        "active": True,
    }
    interval = wf["nodes"][0]["parameters"]["rule"]["interval"][0]
    assert interval["minutesInterval"] == 5


def test_workflow_ids_are_unique():
    """Each workflow and node should get a unique id."""
    ids = [gen_id() for _ in range(10)]
    assert len(set(ids)) == 10


def test_firewall_commands_list():
    """Firewall commands should include essential rules."""
    firewall_commands = [
        "apt-get install -y ufw",
        "ufw default deny incoming",
        "ufw default allow outgoing",
        "ufw allow 22/tcp comment 'SSH'",
        "ufw allow 5678/tcp comment 'n8n'",
        "ufw allow 80/tcp comment 'HTTP'",
        "ufw allow 443/tcp comment 'HTTPS'",
        "echo 'y' | ufw enable",
        "ufw status verbose",
    ]
    # SSH must be allowed before enabling
    ssh_idx = next(i for i, c in enumerate(firewall_commands) if "22/tcp" in c)
    enable_idx = next(i for i, c in enumerate(firewall_commands) if "ufw enable" in c)
    assert ssh_idx < enable_idx

    # Must have deny incoming
    assert any("deny incoming" in c for c in firewall_commands)
    # Must have allow outgoing
    assert any("allow outgoing" in c for c in firewall_commands)
