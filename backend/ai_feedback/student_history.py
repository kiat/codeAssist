import copy
import json


DEFAULT_HISTORY_LIMIT = 5
MAX_HISTORY_LIMIT = 20
MAX_HISTORY_TEXT_CHARS = 1000
TRUNCATION_SUFFIX = "... [truncated]"

LIST_STUDENT_HISTORY_KEYS = (
    "previous_submissions",
    "previous_feedback",
    "previous_conversations",
    "repeated_mistakes",
)
SUMMARY_STUDENT_HISTORY_KEYS = (
    "course_history_summary",
    "assignment_history_summary",
)
STUDENT_HISTORY_CONTEXT_KEYS = (
    *LIST_STUDENT_HISTORY_KEYS,
    *SUMMARY_STUDENT_HISTORY_KEYS,
)
COMMON_HISTORY_ITEM_KEYS = (
    "id",
    "assignment_id",
    "submission_id",
    "created_at",
    "summary",
)
ALLOWED_HISTORY_ITEM_KEYS = {
    "previous_submissions": (
        *COMMON_HISTORY_ITEM_KEYS,
        "submitted_at",
        "score",
        "max_score",
        "mistake_tags",
    ),
    "previous_feedback": (
        *COMMON_HISTORY_ITEM_KEYS,
        "feedback_id",
        "mistake_tags",
        "rubric_breakdown",
    ),
    "previous_conversations": (
        "id",
        "conversation_id",
        "assignment_id",
        "created_at",
        "summary",
        "topics",
    ),
    "repeated_mistakes": (
        "tag",
        "category",
        "summary",
        "count",
        "first_seen_at",
        "last_seen_at",
    ),
}
SENSITIVE_KEY_FRAGMENTS = (
    "api_key",
    "email",
    "message_content",
    "name",
    "raw_code",
    "student",
    "transcript",
)
EMPTY_STUDENT_HISTORY_CONTEXT = {
    "previous_submissions": [],
    "previous_feedback": [],
    "previous_conversations": [],
    "repeated_mistakes": [],
    "course_history_summary": "",
    "assignment_history_summary": "",
}


def empty_student_history_context():
    return copy.deepcopy(EMPTY_STUDENT_HISTORY_CONTEXT)


def normalize_history_limit(limit):
    if isinstance(limit, bool) or not isinstance(limit, int):
        return DEFAULT_HISTORY_LIMIT

    if limit < 0:
        return 0

    return min(limit, MAX_HISTORY_LIMIT)


def _truncate_text(value):
    text = str(value).strip()
    allowed_length = MAX_HISTORY_TEXT_CHARS - len(TRUNCATION_SUFFIX)

    if len(text) <= MAX_HISTORY_TEXT_CHARS:
        return text

    return f"{text[:allowed_length].rstrip()}{TRUNCATION_SUFFIX}"


def _is_empty_history_value(value):
    return value is None or value == "" or value == [] or value == {}


def _is_sensitive_key(key):
    normalized_key = str(key).lower()
    return any(fragment in normalized_key for fragment in SENSITIVE_KEY_FRAGMENTS)


def _safe_history_value(value):
    if value is None:
        return None

    if isinstance(value, str):
        return _truncate_text(value)

    if isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, list):
        safe_values = []
        for item in value:
            safe_value = _safe_history_value(item)
            if not _is_empty_history_value(safe_value):
                safe_values.append(safe_value)
        return safe_values

    if isinstance(value, dict):
        safe_dict = {}
        for item_key, item_value in value.items():
            if _is_sensitive_key(item_key):
                continue

            safe_value = _safe_history_value(item_value)
            if not _is_empty_history_value(safe_value):
                safe_dict[str(item_key)] = safe_value

        return safe_dict

    return _truncate_text(value)


def _normalize_history_item(history_key, item):
    if not isinstance(item, dict):
        return None

    allowed_keys = ALLOWED_HISTORY_ITEM_KEYS[history_key]
    normalized_item = {}

    for item_key in allowed_keys:
        if item_key not in item:
            continue

        safe_value = _safe_history_value(item[item_key])
        if not _is_empty_history_value(safe_value):
            normalized_item[item_key] = safe_value

    return normalized_item or None


def normalize_student_history_context(context, limit=DEFAULT_HISTORY_LIMIT):
    normalized_context = empty_student_history_context()

    if not isinstance(context, dict):
        return normalized_context

    item_limit = normalize_history_limit(limit)

    for key in LIST_STUDENT_HISTORY_KEYS:
        value = context.get(key)
        if isinstance(value, list):
            normalized_items = []

            for item in value:
                normalized_item = _normalize_history_item(key, item)
                if normalized_item:
                    normalized_items.append(normalized_item)

                if len(normalized_items) >= item_limit:
                    break

            normalized_context[key] = normalized_items

    for key in SUMMARY_STUDENT_HISTORY_KEYS:
        value = context.get(key)
        if value is None:
            continue
        normalized_context[key] = _truncate_text(value)

    return normalized_context


def _format_history_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, sort_keys=True)
    return str(value)


def _render_history_list(items):
    return "\n".join(f"- {_format_history_value(item)}" for item in items)


def _section_title(key):
    section_titles = {
        "previous_submissions": "Previous submissions",
        "previous_feedback": "Previous AI feedback",
        "previous_conversations": "Previous AI conversations",
        "repeated_mistakes": "Repeated mistakes",
        "course_history_summary": "Course history summary",
        "assignment_history_summary": "Assignment history summary",
    }

    return section_titles[key]


def _render_history_section(key, value):
    if key in LIST_STUDENT_HISTORY_KEYS:
        rendered_value = _render_history_list(value)
    else:
        rendered_value = value

    return f"{_section_title(key)}:\n{rendered_value}"


def render_student_history_context(context, limit=DEFAULT_HISTORY_LIMIT):
    normalized_context = normalize_student_history_context(context, limit=limit)
    rendered_sections = []

    for key in STUDENT_HISTORY_CONTEXT_KEYS:
        value = normalized_context[key]
        if not value:
            continue

        rendered_sections.append(_render_history_section(key, value))

    if not rendered_sections:
        return "No approved student history context is available."

    return "\n\n".join(rendered_sections)


def build_student_history_retrieval_documents(
    context,
    student_id,
    course_id,
    assignment_id,
    limit=DEFAULT_HISTORY_LIMIT,
):
    if not student_id or not course_id or not assignment_id:
        return []

    normalized_context = normalize_student_history_context(context, limit=limit)
    documents = []

    for key in STUDENT_HISTORY_CONTEXT_KEYS:
        value = normalized_context[key]
        if not value:
            continue

        documents.append(
            {
                "page_content": _render_history_section(key, value),
                "metadata": {
                    "source": f"student_history.{key}",
                    "student_id": str(student_id),
                    "course_id": str(course_id),
                    "assignment_id": str(assignment_id),
                    "history_key": key,
                    "memory_scope": "student_course_assignment",
                },
            }
        )

    return documents


class StudentHistoryService:
    def get_student_history_context(
        self,
        student_id: str,
        course_id: str,
        assignment_id: str,
        limit: int = 5,
    ) -> dict:
        """
        Return historical context for one student in one course.

        This is a future-work interface. It intentionally returns an empty,
        safe structure and does not query production data yet.
        """
        if not student_id or not course_id or not assignment_id:
            return empty_student_history_context()

        normalize_history_limit(limit)

        # TODO: Add permission-checked database queries scoped by student_id,
        # course_id, and assignment_id when student history memory is enabled.
        return empty_student_history_context()
