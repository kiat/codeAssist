from ai_feedback.student_history import (
    StudentHistoryService,
    build_student_history_retrieval_documents,
    normalize_student_history_context,
    render_student_history_context,
)


EXPECTED_EMPTY_CONTEXT = {
    "previous_submissions": [],
    "previous_feedback": [],
    "previous_conversations": [],
    "repeated_mistakes": [],
    "course_history_summary": "",
    "assignment_history_summary": "",
}


def test_student_history_context_returns_safe_empty_default():
    service = StudentHistoryService()

    context = service.get_student_history_context(
        student_id="student-1",
        course_id="course-1",
        assignment_id="assignment-1",
    )

    assert context == EXPECTED_EMPTY_CONTEXT


def test_student_history_context_requires_student_and_course_scope():
    service = StudentHistoryService()

    missing_student_context = service.get_student_history_context(
        student_id="",
        course_id="course-1",
        assignment_id="assignment-1",
    )
    missing_course_context = service.get_student_history_context(
        student_id="student-1",
        course_id=None,
        assignment_id="assignment-1",
    )

    assert missing_student_context == EXPECTED_EMPTY_CONTEXT
    assert missing_course_context == EXPECTED_EMPTY_CONTEXT


def test_student_history_context_has_expected_keys():
    service = StudentHistoryService()

    context = service.get_student_history_context(
        student_id="student-1",
        course_id="course-1",
        assignment_id="assignment-1",
    )

    assert list(context.keys()) == list(EXPECTED_EMPTY_CONTEXT.keys())


def test_student_history_context_returns_fresh_mutable_lists():
    service = StudentHistoryService()

    first_context = service.get_student_history_context(
        student_id="student-1",
        course_id="course-1",
        assignment_id="assignment-1",
    )
    second_context = service.get_student_history_context(
        student_id="student-1",
        course_id="course-1",
        assignment_id="assignment-1",
    )

    first_context["previous_submissions"].append({"id": "submission-1"})

    assert second_context["previous_submissions"] == []


def test_normalize_student_history_context_filters_unknown_keys():
    context = normalize_student_history_context(
        {
            "previous_submissions": [{"id": "submission-1"}],
            "previous_feedback": "not-a-list",
            "previous_conversations": [{"id": "conversation-1"}],
            "repeated_mistakes": [{"tag": "edge_cases"}],
            "course_history_summary": 123,
            "assignment_history_summary": None,
            "other_student_history": [{"student_id": "student-2"}],
        }
    )

    assert context == {
        "previous_submissions": [{"id": "submission-1"}],
        "previous_feedback": [],
        "previous_conversations": [{"id": "conversation-1"}],
        "repeated_mistakes": [{"tag": "edge_cases"}],
        "course_history_summary": "123",
        "assignment_history_summary": "",
    }
    assert "other_student_history" not in context


def test_normalize_student_history_context_returns_fresh_lists():
    raw_context = {
        "previous_submissions": [{"id": "submission-1"}],
    }

    normalized_context = normalize_student_history_context(raw_context)

    raw_context["previous_submissions"].append({"id": "submission-2"})

    assert normalized_context["previous_submissions"] == [{"id": "submission-1"}]


def test_render_student_history_context_returns_safe_empty_message():
    rendered = render_student_history_context(EXPECTED_EMPTY_CONTEXT)

    assert rendered == "No approved student history context is available."


def test_render_student_history_context_formats_only_non_empty_sections():
    rendered = render_student_history_context(
        {
            "previous_submissions": [
                {
                    "assignment_id": "assignment-0",
                    "summary": "Missed the recursive base case.",
                }
            ],
            "previous_feedback": [],
            "previous_conversations": [],
            "repeated_mistakes": [
                {
                    "tag": "edge_cases",
                    "summary": "Often misses boundary conditions.",
                }
            ],
            "course_history_summary": "Improving test coverage over time.",
            "assignment_history_summary": "",
        }
    )

    assert "Previous submissions:" in rendered
    assert "Missed the recursive base case." in rendered
    assert "Repeated mistakes:" in rendered
    assert "Often misses boundary conditions." in rendered
    assert "Course history summary:" in rendered
    assert "Improving test coverage over time." in rendered
    assert "Previous AI feedback:" not in rendered
    assert "Assignment history summary:" not in rendered


def test_normalize_student_history_context_limits_items_and_filters_sensitive_fields():
    context = normalize_student_history_context(
        {
            "previous_submissions": [
                {
                    "id": "submission-1",
                    "assignment_id": "assignment-1",
                    "summary": "Missed the base case.",
                    "student_email": "student@example.com",
                    "raw_code": "print('private source')",
                },
                {
                    "id": "submission-2",
                    "assignment_id": "assignment-2",
                    "summary": "Handled the main path.",
                },
            ],
            "previous_conversations": [
                {
                    "id": "conversation-1",
                    "summary": "Asked about recursion depth.",
                    "message_content": "private chat transcript",
                }
            ],
        },
        limit=1,
    )

    assert context["previous_submissions"] == [
        {
            "id": "submission-1",
            "assignment_id": "assignment-1",
            "summary": "Missed the base case.",
        }
    ]
    assert context["previous_conversations"] == [
        {
            "id": "conversation-1",
            "summary": "Asked about recursion depth.",
        }
    ]
    rendered = render_student_history_context(context)
    assert "student@example.com" not in rendered
    assert "private source" not in rendered
    assert "private chat transcript" not in rendered


def test_normalize_student_history_context_truncates_long_text_values():
    long_summary = "x" * 1300

    context = normalize_student_history_context(
        {
            "repeated_mistakes": [
                {
                    "tag": "edge_cases",
                    "summary": long_summary,
                }
            ],
            "course_history_summary": long_summary,
        }
    )

    mistake_summary = context["repeated_mistakes"][0]["summary"]

    assert len(mistake_summary) < len(long_summary)
    assert mistake_summary.endswith("... [truncated]")
    assert context["course_history_summary"].endswith("... [truncated]")


def test_build_student_history_retrieval_documents_returns_langchain_ready_shape():
    documents = build_student_history_retrieval_documents(
        {
            "previous_feedback": [
                {
                    "id": "feedback-1",
                    "summary": "Suggested more boundary tests.",
                }
            ],
            "repeated_mistakes": [
                {
                    "tag": "edge_cases",
                    "summary": "Often misses boundary conditions.",
                }
            ],
            "course_history_summary": "Improving over time.",
        },
        student_id="student-1",
        course_id="course-1",
        assignment_id="assignment-1",
    )

    assert [document["metadata"]["source"] for document in documents] == [
        "student_history.previous_feedback",
        "student_history.repeated_mistakes",
        "student_history.course_history_summary",
    ]
    assert all("page_content" in document for document in documents)
    assert all(document["metadata"]["student_id"] == "student-1" for document in documents)
    assert all(document["metadata"]["course_id"] == "course-1" for document in documents)
    assert all(document["metadata"]["assignment_id"] == "assignment-1" for document in documents)


def test_build_student_history_retrieval_documents_requires_scope():
    documents = build_student_history_retrieval_documents(
        {
            "course_history_summary": "Improving over time.",
        },
        student_id="",
        course_id="course-1",
        assignment_id="assignment-1",
    )

    assert documents == []
