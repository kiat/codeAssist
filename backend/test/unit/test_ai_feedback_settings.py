from types import SimpleNamespace

import pytest

from ai_feedback.settings import (
    DEFAULT_AI_ALLOWED_INPUTS,
    LEGACY_FEEDBACK_PROMPT_ID,
    build_allowed_feedback_context,
    get_enabled_feedback_prompt,
    normalize_allowed_inputs,
    normalize_feedback_prompts,
    serialize_assignment_ai_settings,
    split_ai_settings_payload,
    update_assignment_ai_settings,
)


def test_normalize_feedback_prompts_returns_default_prompt_set():
    prompts = normalize_feedback_prompts(None)

    assert [prompt["id"] for prompt in prompts] == [
        "check_correctness",
        "debug_failed_tests",
        "review_edge_cases",
        "explain_runtime_errors",
        "review_code_style",
        "suggest_algorithmic_improvements",
    ]
    assert all(prompt["enabled"] is True for prompt in prompts)
    assert all(prompt["title"] for prompt in prompts)
    assert all(prompt["prompt"] for prompt in prompts)


def test_normalize_feedback_prompts_preserves_legacy_single_prompt():
    prompts = normalize_feedback_prompts(None, legacy_prompt="Focus on recursion.")

    assert prompts == [
        {
            "id": LEGACY_FEEDBACK_PROMPT_ID,
            "title": "Custom Feedback",
            "prompt": "Focus on recursion.",
            "enabled": True,
        }
    ]


def test_update_assignment_ai_settings_rejects_empty_prompt_title():
    assignment = SimpleNamespace(ai_feedback_prompts=None, ai_allowed_inputs=None)

    with pytest.raises(ValueError, match="Prompt title is required"):
        update_assignment_ai_settings(
            assignment,
            {
                "feedback_prompts": [
                    {
                        "id": "debug",
                        "title": "",
                        "prompt": "Explain failed tests.",
                        "enabled": True,
                    }
                ],
                "allowed_inputs": DEFAULT_AI_ALLOWED_INPUTS,
            },
        )


def test_get_enabled_feedback_prompt_uses_requested_enabled_prompt():
    assignment = SimpleNamespace(
        ai_feedback_prompt=None,
        ai_feedback_prompts=[
            {
                "id": "disabled_prompt",
                "title": "Disabled",
                "prompt": "Do not use this.",
                "enabled": False,
            },
            {
                "id": "debug_failed_tests",
                "title": "Debug Failed Tests",
                "prompt": "Explain failed tests.",
                "enabled": True,
            },
        ],
    )

    prompt = get_enabled_feedback_prompt(assignment, "debug_failed_tests")

    assert prompt["title"] == "Debug Failed Tests"
    assert prompt["prompt"] == "Explain failed tests."


def test_get_enabled_feedback_prompt_rejects_disabled_prompt():
    assignment = SimpleNamespace(
        ai_feedback_prompt=None,
        ai_feedback_prompts=[
            {
                "id": "debug_failed_tests",
                "title": "Debug Failed Tests",
                "prompt": "Explain failed tests.",
                "enabled": False,
            }
        ],
    )

    with pytest.raises(ValueError, match="not enabled"):
        get_enabled_feedback_prompt(assignment, "debug_failed_tests")


def test_normalize_allowed_inputs_merges_defaults_and_booleans():
    allowed_inputs = normalize_allowed_inputs(
        {
            "student_code": False,
            "test_cases": True,
            "unknown": True,
        }
    )

    assert allowed_inputs == {
        "assignment_description": True,
        "student_code": False,
        "test_results": True,
        "test_cases": True,
        "student_output": True,
    }


def test_split_ai_settings_payload_separates_settings_without_mutating_source():
    payload = {
        "name": "Loops",
        "course_id": "course-1",
        "ai_feedback_enabled": True,
        "feedback_prompts": [
            {
                "id": "debug",
                "title": "Debug",
                "prompt": "Explain failed tests.",
                "enabled": True,
            }
        ],
        "allowed_inputs": {"student_code": False},
    }

    assignment_payload, ai_settings_payload = split_ai_settings_payload(payload)

    assert assignment_payload == {
        "name": "Loops",
        "course_id": "course-1",
    }
    assert ai_settings_payload == {
        "ai_feedback_enabled": True,
        "feedback_prompts": payload["feedback_prompts"],
        "allowed_inputs": {"student_code": False},
    }
    assert "feedback_prompts" in payload


def test_build_allowed_feedback_context_excludes_unapproved_code_and_outputs():
    assignment = SimpleNamespace(
        name="Recursion Lab",
        description="Practice recursive functions.",
        ai_allowed_inputs={
            "assignment_description": True,
            "student_code": False,
            "test_results": True,
            "test_cases": False,
            "student_output": False,
        },
    )

    context = build_allowed_feedback_context(
        assignment=assignment,
        code_text="print('secret implementation')",
        autograder_results={
            "tests": [
                {
                    "name": "base case",
                    "status": "failed",
                    "score": 0,
                    "max_score": 1,
                    "input": "3",
                    "expected_output": "6",
                    "output": "0",
                }
            ],
            "score": 0,
            "output": "student stdout",
        },
    )

    rendered = "\n".join(context.values())

    assert "Practice recursive functions." in rendered
    assert "base case" in rendered
    assert "print('secret implementation')" not in rendered
    assert "expected_output" not in rendered
    assert "student stdout" not in rendered
    assert '"output"' not in context["test_results"]


def test_serialize_assignment_ai_settings_combines_existing_model_and_feedback_settings():
    assignment = SimpleNamespace(
        ai_feedback_enabled=True,
        use_course_ai_default=False,
        ai_feedback_provider="gemini",
        ai_feedback_model="gemini-1.5-flash",
        ai_feedback_prompt=None,
        ai_feedback_prompts=[
            {
                "id": "edge_cases",
                "title": "Edge Cases",
                "prompt": "Review edge cases.",
                "enabled": True,
            }
        ],
        ai_feedback_temperature=0.3,
        ai_feedback_style="balanced",
        ai_allowed_inputs={"student_code": False},
    )

    settings = serialize_assignment_ai_settings(assignment)

    assert settings["ai_feedback_enabled"] is True
    assert settings["use_course_ai_default"] is False
    assert settings["ai_feedback_provider"] == "gemini"
    assert settings["ai_feedback_model"] == "gemini-1.5-flash"
    assert settings["feedback_prompts"][0]["id"] == "edge_cases"
    assert settings["allowed_inputs"]["student_code"] is False
