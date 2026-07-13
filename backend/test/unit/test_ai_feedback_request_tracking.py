"""Tests for AI feedback request tracking (Issue #328)."""
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

import pytest

from ai_feedback.settings import (
    check_feedback_limits,
    get_student_feedback_status,
    record_feedback_request,
)


def _make_assignment(**kwargs):
    """Helper to create a mock assignment with AI feedback settings."""
    defaults = {
        "id": "asgn-1",
        "ai_feedback_enabled": True,
        "ai_feedback_max_requests": None,
        "ai_feedback_wait_seconds": 0,
        "ai_feedback_prompts": None,
        "ai_feedback_prompt": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# check_feedback_limits
# ---------------------------------------------------------------------------


def test_check_feedback_limits_allows_when_no_limits_set(mocker):
    """No max_requests or wait_seconds set -> always allowed."""
    assignment = _make_assignment()
    mock_query = mocker.patch("api.db.session.query")
    mock_query.return_value.filter_by.return_value.count.return_value = 0

    result = check_feedback_limits(assignment, "student-1")

    assert result["allowed"] is True
    assert result["remaining"] is None
    assert result["wait_seconds"] == 0


def test_check_feedback_limits_rejects_when_max_requests_zero(mocker):
    """max_requests=0 -> feedback disabled."""
    assignment = _make_assignment(ai_feedback_max_requests=0)
    mock_query = mocker.patch("api.db.session.query")
    mock_query.return_value.filter_by.return_value.count.return_value = 0

    result = check_feedback_limits(assignment, "student-1")

    assert result["allowed"] is False
    assert result["remaining"] == 0
    assert "disabled" in result["message"].lower()


def test_check_feedback_limits_allows_when_under_limit(mocker):
    """max_requests=5, used 2 -> allowed with remaining=3."""
    assignment = _make_assignment(ai_feedback_max_requests=5)
    mock_query = mocker.patch("api.db.session.query")
    mock_query.return_value.filter_by.return_value.count.return_value = 2

    result = check_feedback_limits(assignment, "student-1")

    assert result["allowed"] is True
    assert result["remaining"] == 3


def test_check_feedback_limits_rejects_when_at_limit(mocker):
    """max_requests=3, used 3 -> rejected."""
    assignment = _make_assignment(ai_feedback_max_requests=3)
    mock_query = mocker.patch("api.db.session.query")
    mock_query.return_value.filter_by.return_value.count.return_value = 3

    result = check_feedback_limits(assignment, "student-1")

    assert result["allowed"] is False
    assert result["remaining"] == 0
    assert "used all" in result["message"].lower()


def test_check_feedback_limits_rejects_during_cooldown(mocker):
    """wait_seconds=60, last request was 30s ago -> rejected with wait_seconds=30."""
    assignment = _make_assignment(ai_feedback_wait_seconds=60)
    now = datetime.now(timezone.utc)

    last_request = SimpleNamespace(created_at=now - timedelta(seconds=30))

    mock_query = mocker.patch("api.db.session.query")
    # First call: count -> 1
    # Second call: order_by().first() -> last_request
    mock_query.return_value.filter_by.return_value.count.return_value = 1
    mock_query.return_value.filter_by.return_value.order_by.return_value.first.return_value = last_request

    result = check_feedback_limits(assignment, "student-1")

    assert result["allowed"] is False
    assert result["wait_seconds"] >= 29
    assert "wait" in result["message"].lower()


def test_check_feedback_limits_allows_after_cooldown(mocker):
    """wait_seconds=60, last request was 90s ago -> allowed."""
    assignment = _make_assignment(ai_feedback_wait_seconds=60)
    now = datetime.now(timezone.utc)

    last_request = SimpleNamespace(created_at=now - timedelta(seconds=90))

    mock_query = mocker.patch("api.db.session.query")
    mock_query.return_value.filter_by.return_value.count.return_value = 1
    mock_query.return_value.filter_by.return_value.order_by.return_value.first.return_value = last_request

    result = check_feedback_limits(assignment, "student-1")

    assert result["allowed"] is True
    assert result["wait_seconds"] == 0


def test_check_feedback_limits_no_cooldown_on_first_request(mocker):
    """wait_seconds=60 but no previous requests -> allowed (first request)."""
    assignment = _make_assignment(ai_feedback_wait_seconds=60)
    mock_query = mocker.patch("api.db.session.query")
    mock_query.return_value.filter_by.return_value.count.return_value = 0

    result = check_feedback_limits(assignment, "student-1")

    assert result["allowed"] is True
    assert result["wait_seconds"] == 0


# ---------------------------------------------------------------------------
# get_student_feedback_status
# ---------------------------------------------------------------------------


def test_get_student_feedback_status_returns_unlimited(mocker):
    """No limits set -> remaining is None."""
    assignment = _make_assignment()
    mock_query = mocker.patch("api.db.session.query")
    mock_query.return_value.filter_by.return_value.count.return_value = 0

    status = get_student_feedback_status(assignment, "student-1")

    assert status["remaining"] is None
    assert status["wait_seconds"] == 0
    assert status["max_requests"] is None
    assert status["total_requests"] == 0


def test_get_student_feedback_status_returns_remaining(mocker):
    """max_requests=10, used 4 -> remaining=6."""
    assignment = _make_assignment(ai_feedback_max_requests=10)
    mock_query = mocker.patch("api.db.session.query")
    mock_query.return_value.filter_by.return_value.count.return_value = 4

    status = get_student_feedback_status(assignment, "student-1")

    assert status["remaining"] == 6
    assert status["total_requests"] == 4


def test_get_student_feedback_status_returns_wait_remaining(mocker):
    """wait_seconds=120, last request 50s ago -> wait_seconds=70."""
    assignment = _make_assignment(ai_feedback_wait_seconds=120)
    now = datetime.now(timezone.utc)
    last_request = SimpleNamespace(created_at=now - timedelta(seconds=50))

    mock_query = mocker.patch("api.db.session.query")
    mock_query.return_value.filter_by.return_value.count.return_value = 1
    mock_query.return_value.filter_by.return_value.order_by.return_value.first.return_value = last_request

    status = get_student_feedback_status(assignment, "student-1")

    assert status["wait_seconds"] >= 69
    assert status["remaining"] is None  # no max_requests set


# ---------------------------------------------------------------------------
# record_feedback_request
# ---------------------------------------------------------------------------


def test_record_feedback_request_creates_record(mocker):
    """record_feedback_request should add and commit a new AIFeedbackRequest."""
    mock_add = mocker.patch("api.db.session.add")
    mock_commit = mocker.patch("api.db.session.commit")

    record_feedback_request("student-1", "asgn-1", "debug_failed_tests")

    mock_add.assert_called_once()
    mock_commit.assert_called_once()

    # Verify the record has correct fields
    record = mock_add.call_args[0][0]
    assert record.student_id == "student-1"
    assert record.assignment_id == "asgn-1"
    assert record.prompt_id == "debug_failed_tests"
    assert record.id  # should have a UUID
    assert record.created_at  # should have a timestamp


def test_record_feedback_request_works_without_prompt_id(mocker):
    """record_feedback_request should work without a prompt_id."""
    mock_add = mocker.patch("api.db.session.add")
    mock_commit = mocker.patch("api.db.session.commit")

    record_feedback_request("student-1", "asgn-1")

    record = mock_add.call_args[0][0]
    assert record.prompt_id is None
