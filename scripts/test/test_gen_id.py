"""Tests for gen_id() in fase2_deploy.py

gen_id generates random 16-char alphanumeric IDs for workflow nodes.
"""

from deploy.fase2_deploy import gen_id


def test_gen_id_returns_string():
    assert isinstance(gen_id(), str)


def test_gen_id_length():
    assert len(gen_id()) == 16


def test_gen_id_alphanumeric():
    assert gen_id().isalnum()


def test_gen_id_unique():
    ids = {gen_id() for _ in range(50)}
    assert len(ids) == 50


def test_gen_id_no_special_chars():
    for _ in range(20):
        result = gen_id()
        assert all(c.isalpha() or c.isdigit() for c in result)
