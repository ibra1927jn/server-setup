"""Tests for rebuild_v2.py credential extraction, workflow structures, and line parsing."""
import json


# --- Credential extraction logic (mirrors rebuild_v2.py lines 17-21) ---

def _extract_credentials(creds):
    """Extract telegram and SSH credentials from n8n credential list."""
    tg_cred = None
    ssh_cred = None
    for c in creds:
        if c["type"] == "telegramApi":
            tg_cred = {"id": c["id"], "name": c["name"]}
        if c["type"] == "sshPassword":
            ssh_cred = {"id": c["id"], "name": c["name"]}
    return tg_cred, ssh_cred


def test_extract_both_credentials():
    creds = [
        {"id": "1", "name": "TG Bot", "type": "telegramApi"},
        {"id": "2", "name": "SSH Root", "type": "sshPassword"},
    ]
    tg, ssh = _extract_credentials(creds)
    assert tg == {"id": "1", "name": "TG Bot"}
    assert ssh == {"id": "2", "name": "SSH Root"}


def test_extract_missing_ssh():
    creds = [{"id": "1", "name": "TG Bot", "type": "telegramApi"}]
    tg, ssh = _extract_credentials(creds)
    assert tg is not None
    assert ssh is None


def test_extract_missing_telegram():
    creds = [{"id": "2", "name": "SSH", "type": "sshPassword"}]
    tg, ssh = _extract_credentials(creds)
    assert tg is None
    assert ssh is not None


def test_extract_empty_credentials():
    tg, ssh = _extract_credentials([])
    assert tg is None
    assert ssh is None


def test_extract_unrelated_credentials():
    creds = [
        {"id": "3", "name": "SMTP", "type": "smtp"},
        {"id": "4", "name": "HTTP", "type": "httpBasicAuth"},
    ]
    tg, ssh = _extract_credentials(creds)
    assert tg is None
    assert ssh is None


def test_extract_last_wins_on_duplicate():
    """If multiple creds of same type, last one wins."""
    creds = [
        {"id": "1", "name": "TG Old", "type": "telegramApi"},
        {"id": "2", "name": "TG New", "type": "telegramApi"},
    ]
    tg, _ = _extract_credentials(creds)
    assert tg["id"] == "2"


# --- Workflow ID mapping (mirrors rebuild_v2.py lines 26-31) ---

def _build_wf_id_map(existing_workflows):
    """Build name->id mapping from exported workflows."""
    wf_ids = {}
    for wf in existing_workflows:
        wf_ids[wf["name"]] = wf["id"]
    return wf_ids


def test_build_wf_id_map():
    existing = [
        {"name": "Crypto Portfolio Alerts", "id": "abc"},
        {"name": "Daily Briefing", "id": "def"},
    ]
    result = _build_wf_id_map(existing)
    assert result == {"Crypto Portfolio Alerts": "abc", "Daily Briefing": "def"}


def test_build_wf_id_map_empty():
    assert _build_wf_id_map([]) == {}


# --- Workflow structure validation ---

def _make_crypto_workflow(wf_id, chat_id, tg_cred):
    """Build Crypto Portfolio Alerts workflow (mirrors rebuild_v2.py lines 37-80)."""
    return {
        "id": wf_id,
        "name": "Crypto Portfolio Alerts",
        "active": True,
        "nodes": [
            {
                "parameters": {"rule": {"interval": [{"field": "hours", "hoursInterval": 1}]}},
                "name": "Every Hour",
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [250, 300],
                "id": "node1",
            },
            {
                "parameters": {
                    "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,ripple,dogecoin&vs_currencies=usd&include_24hr_change=true",
                    "options": {},
                },
                "name": "Get Prices",
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.2,
                "position": [470, 300],
                "id": "node2",
            },
            {
                "parameters": {
                    "chatId": chat_id,
                    "text": "=Crypto Portfolio",
                    "additionalFields": {"parse_mode": "Markdown"},
                },
                "name": "Send Telegram",
                "type": "n8n-nodes-base.telegram",
                "typeVersion": 1.2,
                "position": [690, 300],
                "id": "node3",
                "credentials": {"telegramApi": tg_cred},
            },
        ],
        "connections": {
            "Every Hour": {"main": [[{"node": "Get Prices", "type": "main", "index": 0}]]},
            "Get Prices": {"main": [[{"node": "Send Telegram", "type": "main", "index": 0}]]},
        },
    }


def test_crypto_workflow_has_3_nodes():
    wf = _make_crypto_workflow("id1", "123", {"id": "t1", "name": "TG"})
    assert len(wf["nodes"]) == 3


def test_crypto_workflow_connections_match_nodes():
    wf = _make_crypto_workflow("id1", "123", {"id": "t1", "name": "TG"})
    node_names = {n["name"] for n in wf["nodes"]}
    for source in wf["connections"]:
        assert source in node_names, f"Connection source '{source}' not in nodes"
        for conn_list in wf["connections"][source]["main"]:
            for conn in conn_list:
                assert conn["node"] in node_names, f"Target '{conn['node']}' not in nodes"


def test_crypto_workflow_is_json_serializable():
    wf = _make_crypto_workflow("id1", "123", {"id": "t1", "name": "TG"})
    serialized = json.dumps(wf)
    restored = json.loads(serialized)
    assert restored["name"] == "Crypto Portfolio Alerts"


def test_crypto_workflow_uses_chat_id():
    wf = _make_crypto_workflow("id1", "CHAT456", {"id": "t1", "name": "TG"})
    tg_node = [n for n in wf["nodes"] if n["name"] == "Send Telegram"][0]
    assert tg_node["parameters"]["chatId"] == "CHAT456"


def test_crypto_workflow_credential_ref():
    cred = {"id": "cred-xyz", "name": "My TG Bot"}
    wf = _make_crypto_workflow("id1", "123", cred)
    tg_node = [n for n in wf["nodes"] if n["name"] == "Send Telegram"][0]
    assert tg_node["credentials"]["telegramApi"] == cred


# --- Workflow filename generation (mirrors rebuild_v2.py line 226) ---

def _workflow_filename(name):
    """Generate filename for workflow export."""
    return f"update_{name.lower().replace(' ', '_')}.json"


def test_filename_crypto():
    assert _workflow_filename("Crypto Portfolio Alerts") == "update_crypto_portfolio_alerts.json"


def test_filename_daily():
    assert _workflow_filename("Daily Briefing") == "update_daily_briefing.json"


def test_filename_uptime():
    assert _workflow_filename("Uptime Monitor") == "update_uptime_monitor.json"


def test_filename_github():
    assert _workflow_filename("GitHub Auto-Backup") == "update_github_auto-backup.json"


# --- Pipe-delimited line parsing (mirrors final_pendientes.py lines 23-27) ---

def _parse_workflow_list(lines):
    """Parse n8n list:workflow output (pipe-delimited)."""
    results = []
    for line in lines:
        if "|" in line:
            wf_id = line.split("|")[0].strip()
            wf_name = line.split("|")[1].strip()
            results.append((wf_id, wf_name))
    return results


def test_parse_typical_output():
    lines = [
        "abc123 | Crypto Portfolio Alerts | active",
        "def456 | Daily Briefing | active",
    ]
    result = _parse_workflow_list(lines)
    assert result == [("abc123", "Crypto Portfolio Alerts"), ("def456", "Daily Briefing")]


def test_parse_empty_lines():
    assert _parse_workflow_list([]) == []


def test_parse_no_pipe_lines():
    lines = ["header line", "another line"]
    assert _parse_workflow_list(lines) == []


def test_parse_extra_whitespace():
    lines = ["  id1  |  My Workflow  | active"]
    result = _parse_workflow_list(lines)
    assert result == [("id1", "My Workflow")]


def test_parse_mixed_lines():
    lines = [
        "n8n CLI output header",
        "abc | Workflow One | active",
        "",
        "def | Workflow Two | inactive",
    ]
    result = _parse_workflow_list(lines)
    assert len(result) == 2


# --- Reset password template (mirrors reset_pw_v3.py line 43) ---

def _inject_password(template, password):
    """Replace placeholder with actual password."""
    return template.replace("__N8N_PW__", password)


def test_inject_simple():
    tmpl = "hash('__N8N_PW__')"
    assert _inject_password(tmpl, "mypass") == "hash('mypass')"


def test_inject_special_chars():
    tmpl = "hash('__N8N_PW__')"
    result = _inject_password(tmpl, "p@ss'w0rd!")
    assert "p@ss'w0rd!" in result


def test_inject_preserves_rest():
    tmpl = "before __N8N_PW__ middle __N8N_PW__ after"
    result = _inject_password(tmpl, "X")
    assert result == "before X middle X after"


def test_inject_no_placeholder():
    tmpl = "no placeholder here"
    assert _inject_password(tmpl, "pass") == "no placeholder here"
