def test_ai_feedback_modules_are_importable_from_package():
    from ai_feedback.integration import DEFAULT_FEEDBACK_PROMPT
    from ai_feedback.settings import DEFAULT_AI_ALLOWED_INPUTS

    assert "Overall Summary" in DEFAULT_FEEDBACK_PROMPT
    assert DEFAULT_AI_ALLOWED_INPUTS["student_code"] is True
