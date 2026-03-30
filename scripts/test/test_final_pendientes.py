"""Tests for final_pendientes.py parse_workflow_ids function"""
from final_pendientes import parse_workflow_ids


def test_parse_single_workflow():
    output = "abc123 | Daily Briefing"
    result = parse_workflow_ids(output)
    assert result == [("abc123", "Daily Briefing")]


def test_parse_multiple_workflows():
    output = "id1 | Workflow One\nid2 | Workflow Two\nid3 | Workflow Three"
    result = parse_workflow_ids(output)
    assert len(result) == 3
    assert result[0] == ("id1", "Workflow One")
    assert result[2] == ("id3", "Workflow Three")


def test_parse_empty_string():
    assert parse_workflow_ids("") == []


def test_parse_no_pipe_lines():
    output = "some header line\nanother line\n"
    assert parse_workflow_ids(output) == []


def test_parse_mixed_lines():
    output = "Header\nabc | My Flow\nfooter"
    result = parse_workflow_ids(output)
    assert result == [("abc", "My Flow")]


def test_parse_strips_whitespace():
    output = "  id1  |  Spaced Name  "
    result = parse_workflow_ids(output)
    assert result == [("id1", "Spaced Name")]


def test_parse_extra_pipes():
    output = "id1 | Name | extra"
    result = parse_workflow_ids(output)
    assert result[0][0] == "id1"
    assert result[0][1] == "Name"


def test_parse_only_whitespace():
    assert parse_workflow_ids("   \n  \n") == []
