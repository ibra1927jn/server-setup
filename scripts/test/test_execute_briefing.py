"""Tests for execute_daily_briefing.py find_workflow_id function"""
from execute_daily_briefing import find_workflow_id


def test_find_existing_workflow():
    workflows = [
        {"name": "Daily Briefing", "id": "abc123"},
        {"name": "Uptime Monitor", "id": "def456"},
    ]
    assert find_workflow_id(workflows, "Daily Briefing") == "abc123"


def test_find_second_workflow():
    workflows = [
        {"name": "Daily Briefing", "id": "abc123"},
        {"name": "Uptime Monitor", "id": "def456"},
    ]
    assert find_workflow_id(workflows, "Uptime Monitor") == "def456"


def test_workflow_not_found():
    workflows = [
        {"name": "Daily Briefing", "id": "abc123"},
    ]
    assert find_workflow_id(workflows, "Nonexistent") is None


def test_empty_list():
    assert find_workflow_id([], "Daily Briefing") is None


def test_workflow_missing_name():
    workflows = [{"id": "abc123"}]
    assert find_workflow_id(workflows, "Daily Briefing") is None


def test_workflow_missing_id():
    workflows = [{"name": "Daily Briefing"}]
    assert find_workflow_id(workflows, "Daily Briefing") is None
