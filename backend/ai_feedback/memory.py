import json
import uuid

from api import db
from api.models import StudentSubmissionInsight


MAX_INSIGHT_SUMMARY_CHARS = 2000
MAX_RENDERED_HISTORY_CHARS = 12000
DEFAULT_SUBMISSION_HISTORY_LIMIT = 5


def _truncate_text(text, limit):
    text = str(text or "").strip()
    if len(text) <= limit:
        return text

    return f"{text[:limit].rstrip()}..."


def _json_safe(value):
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def _format_insight_item(item):
    if isinstance(item, str):
        return item.strip()

    if isinstance(item, (dict, list)):
        return json.dumps(item, sort_keys=True)

    if item is None:
        return ""

    return str(item).strip()


def summarize_insights(insights):
    """Return a compact, readable summary from provider insight output."""
    if insights is None:
        return ""

    if isinstance(insights, str):
        return _truncate_text(insights, MAX_INSIGHT_SUMMARY_CHARS)

    items = insights if isinstance(insights, list) else [insights]
    lines = []

    for item in items:
        text = _format_insight_item(item)
        if text:
            lines.append(f"- {text}")

    return _truncate_text("\n".join(lines), MAX_INSIGHT_SUMMARY_CHARS)


def record_submission_insight(submission, insights):
    """Create or update the insight record for one AI-reviewed submission."""
    summary = summarize_insights(insights)
    if not summary:
        return None

    record = StudentSubmissionInsight.query.filter_by(
        submission_id=submission.id
    ).first()

    if not record:
        record = StudentSubmissionInsight(
            id=str(uuid.uuid4()),
            submission_id=submission.id,
        )

    record.student_id = submission.student_id
    record.assignment_id = submission.assignment_id
    record.insights = _json_safe(insights)
    record.summary = summary

    db.session.add(record)
    return record


def get_recent_submission_insights(student_id, assignment_id=None, limit=None):
    """Load recent submission insight records for prompt memory."""
    limit = DEFAULT_SUBMISSION_HISTORY_LIMIT if limit is None else limit
    if not student_id or limit <= 0:
        return []

    query = StudentSubmissionInsight.query.filter_by(student_id=student_id)

    if assignment_id:
        query = query.filter_by(assignment_id=assignment_id)

    return (
        query.order_by(StudentSubmissionInsight.created_at.desc())
        .limit(limit)
        .all()
    )


def render_submission_insight_history(records):
    """Render insight records in chronological order for the model prompt."""
    records = list(records or [])
    if not records:
        return ""

    sections = []

    for record in reversed(records):
        assignment = getattr(record, "assignment", None)
        submission = getattr(record, "submission", None)

        label_parts = []
        assignment_name = getattr(assignment, "name", None)
        submitted_at = getattr(submission, "submitted_at", None)

        if assignment_name:
            label_parts.append(str(assignment_name))
        if submitted_at:
            label_parts.append(str(submitted_at))

        label = " - ".join(label_parts) or str(record.submission_id)
        summary = record.summary or summarize_insights(record.insights)
        if summary:
            sections.append(f"Submission {label}:\n{summary}")

    return _truncate_text("\n\n".join(sections), MAX_RENDERED_HISTORY_CHARS)


def get_recent_submission_history_text(student_id, assignment_id=None, limit=None):
    records = get_recent_submission_insights(
        student_id,
        assignment_id=assignment_id,
        limit=limit,
    )
    return render_submission_insight_history(records)
