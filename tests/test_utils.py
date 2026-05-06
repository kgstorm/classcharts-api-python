"""Tests for utility functions."""

import pytest
from classcharts_api.utils import (
    is_homework_ticked,
    is_homework_unticked,
    parse_cookies,
)


def test_parse_cookies_single():
    raw = "session=abc123; Path=/"
    result = parse_cookies(raw)
    assert result["session"] == "abc123"


def test_parse_cookies_multiple():
    raw = "parent_session_credentials=%7B%22session_id%22%3A%22xyz%22%7D; Path=/, other=val; Path=/"
    result = parse_cookies(raw)
    assert result["parent_session_credentials"] == '{"session_id":"xyz"}'
    assert result["other"] == "val"


def test_parse_cookies_trims_whitespace():
    raw = "  key=value; Path=/"
    result = parse_cookies(raw)
    assert "key" in result


def test_homework_ticked_false_when_not_ticked():
    homework = {"status": {"ticked": "no", "state": None}}
    assert is_homework_ticked(homework) is False
    assert is_homework_unticked(homework) is True


def test_homework_ticked_true_when_ticked_yes_state_null():
    homework = {"status": {"ticked": "yes", "state": None}}
    assert is_homework_ticked(homework) is True
    assert is_homework_unticked(homework) is False


def test_homework_ticked_true_when_ticked_yes_state_completed():
    homework = {"status": {"ticked": "yes", "state": "completed"}}
    assert is_homework_ticked(homework) is True
    assert is_homework_unticked(homework) is False


def test_homework_ticked_defaults_false_for_missing_status():
    homework = {"id": 123}
    assert is_homework_ticked(homework) is False
    assert is_homework_unticked(homework) is True
