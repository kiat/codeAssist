from types import SimpleNamespace

import pytest
import requests

from ai_feedback.integration import (
    DEFAULT_FEEDBACK_PROMPT,
    RETURN_SPEC,
    build_claude_messages_payload,
    build_feedback_prompt,
    get_provider_credentials,
    get_structured_feedback_from_claude,
    get_structured_feedback_from_gemini,
    parse_feedback_json,
)


def test_default_feedback_prompt_asks_for_professional_feedback_even_when_tests_pass():
    assert "Always provide useful feedback" in DEFAULT_FEEDBACK_PROMPT
    assert "Overall Summary" in DEFAULT_FEEDBACK_PROMPT
    assert "Correctness Feedback" in DEFAULT_FEEDBACK_PROMPT
    assert "Improvement Suggestions" in DEFAULT_FEEDBACK_PROMPT


def test_return_spec_keeps_insights_for_every_submission():
    assert "Include general insights for every submission" in RETURN_SPEC
    assert "annotations only when line-specific feedback is helpful" in RETURN_SPEC
    assert "Use a single-line code pattern" in RETURN_SPEC


def test_build_feedback_prompt_uses_professional_default_prompt():
    prompt = build_feedback_prompt(
        base_prompt="",
        past_insights="No prior insights.",
        code="print('hello')",
        autograder_results='{"tests":[]}',
        style_instruction="Feedback style: balanced.",
    )

    assert "Always provide useful feedback" in prompt
    assert "Improvement Suggestions" in prompt


def test_build_feedback_prompt_uses_filtered_context_without_old_code_block():
    prompt = build_feedback_prompt(
        base_prompt="Review this submission.",
        past_insights="No prior insights.",
        code="print('secret implementation')",
        autograder_results='{"output":"secret stdout"}',
        style_instruction="Feedback style: balanced.",
        feedback_context={
            "assignment_description": "Practice recursion.",
            "test_results": '{"score": 1}',
        },
    )

    assert "Practice recursion." in prompt
    assert '{"score": 1}' in prompt
    assert "Student code:" not in prompt
    assert prompt.count("Autograder results:") == 1
    assert "print('secret implementation')" not in prompt
    assert "secret stdout" not in prompt


def test_parse_feedback_json_accepts_escaped_newlines_inside_code_patterns():
    raw_response = (
        '{"insights":["Overall Summary: Feedback is available."],'
        '"annotations":[{"pattern":"def create_spiral(n):\\n    print(\\"TODO\\")",'
        '"comment":"Add the missing implementation for this function."}]}'
    )

    parsed, new_insights = parse_feedback_json(
        raw_response,
        "Claude",
        "No prior insights.",
    )

    assert "error" not in parsed
    assert parsed["annotations"][0]["pattern"] == 'def create_spiral(n):\n    print("TODO")'
    assert new_insights == ["Overall Summary: Feedback is available."]


def test_parse_feedback_json_extracts_json_object_from_provider_wrapper_text():
    raw_response = (
        "Here is the requested JSON:\n"
        '{"insights":["Correctness Feedback: Tests failed."],"annotations":[]}\n'
        "No additional comments."
    )

    parsed, new_insights = parse_feedback_json(
        raw_response,
        "Gemini",
        "No prior insights.",
    )

    assert "error" not in parsed
    assert parsed["insights"] == ["Correctness Feedback: Tests failed."]
    assert new_insights == ["Correctness Feedback: Tests failed."]


def test_parse_feedback_json_escapes_literal_newlines_inside_provider_strings():
    raw_response = """{
  "insights": [
    "Overall Summary: The submission contains significant
issues that should be fixed."
  ],
  "annotations": [
    {
      "pattern": "def create_spiral(dim):
    # ADD YOUR CODE HERE",
      "comment": "Function body is empty."
    }
  ]
}"""

    parsed, new_insights = parse_feedback_json(
        raw_response,
        "Claude",
        "No prior insights.",
    )

    assert "error" not in parsed
    assert parsed["insights"] == [
        "Overall Summary: The submission contains significant\nissues that should be fixed."
    ]
    assert parsed["annotations"][0]["pattern"] == (
        "def create_spiral(dim):\n    # ADD YOUR CODE HERE"
    )
    assert new_insights == parsed["insights"]


def test_gemini_feedback_request_reserves_tokens_for_json(monkeypatch):
    captured_request = {}

    class FakeGeminiResponse:
        status_code = 200
        text = ""

        def json(self):
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": (
                                        '{"insights":["Overall Summary: Feedback is ready."],'
                                        '"annotations":[]}'
                                    )
                                }
                            ]
                        }
                    }
                ]
            }

    def fake_post(url, params, json, timeout):
        captured_request["json"] = json
        return FakeGeminiResponse()

    monkeypatch.setattr("ai_feedback.integration.requests.post", fake_post)

    parsed, new_insights = get_structured_feedback_from_gemini(
        api_key="gemini-key",
        prompt="Return JSON feedback.",
        model="gemini-2.5-flash",
        temperature=0.5,
        past_insights=[],
    )

    generation_config = captured_request["json"]["generationConfig"]

    assert "error" not in parsed
    assert new_insights == ["Overall Summary: Feedback is ready."]
    assert generation_config["maxOutputTokens"] >= 1400
    assert generation_config["thinkingConfig"]["thinkingBudget"] == 0


def test_gemini_feedback_retries_transient_unavailable(monkeypatch, capsys):
    calls = []
    sleeps = []

    class FakeGeminiResponse:
        def __init__(self, status_code, text, payload):
            self.status_code = status_code
            self.text = text
            self._payload = payload

        def json(self):
            return self._payload

    def fake_post(url, params, json, timeout):
        calls.append({"url": url, "params": params, "json": json, "timeout": timeout})
        if len(calls) == 1:
            return FakeGeminiResponse(
                503,
                '{"error":{"status":"UNAVAILABLE"}}',
                {"error": {"status": "UNAVAILABLE"}},
            )
        return FakeGeminiResponse(
            200,
            "",
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": (
                                        '{"insights":["Overall Summary: Feedback recovered."],'
                                        '"annotations":[]}'
                                    )
                                }
                            ]
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr("ai_feedback.integration.requests.post", fake_post)
    monkeypatch.setattr(
        "ai_feedback.integration.time.sleep",
        lambda seconds: sleeps.append(seconds),
    )

    parsed, new_insights = get_structured_feedback_from_gemini(
        api_key="gemini-key",
        prompt="Return JSON feedback.",
        model="gemini-2.5-flash",
        temperature=0.5,
        past_insights=[],
    )

    assert len(calls) == 2
    assert "error" not in parsed
    assert new_insights == ["Overall Summary: Feedback recovered."]
    assert sleeps == [1]
    assert "GEMINI_RETRY: status 503" in capsys.readouterr().out


def test_gemini_feedback_retries_transient_network_error(monkeypatch):
    calls = []
    sleeps = []

    class FakeGeminiResponse:
        status_code = 200
        text = ""

        def json(self):
            return {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": (
                                        '{"insights":["Overall Summary: Feedback recovered after timeout."],'
                                        '"annotations":[]}'
                                    )
                                }
                            ]
                        }
                    }
                ]
            }

    def fake_post(url, params, json, timeout):
        calls.append({"url": url, "params": params, "json": json, "timeout": timeout})
        if len(calls) == 1:
            raise requests.Timeout("temporary timeout")
        return FakeGeminiResponse()

    monkeypatch.setattr("ai_feedback.integration.requests.post", fake_post)
    monkeypatch.setattr(
        "ai_feedback.integration.time.sleep",
        lambda seconds: sleeps.append(seconds),
    )

    parsed, new_insights = get_structured_feedback_from_gemini(
        api_key="gemini-key",
        prompt="Return JSON feedback.",
        model="gemini-2.5-flash",
        temperature=0.5,
        past_insights=[],
    )

    assert len(calls) == 2
    assert sleeps == [1]
    assert "error" not in parsed
    assert new_insights == ["Overall Summary: Feedback recovered after timeout."]


def test_claude_messages_payload_omits_temperature():
    payload = build_claude_messages_payload(
        model="claude-sonnet-5",
        max_tokens=700,
        system_prompt="Return JSON.",
        user_prompt="Review this code.",
    )

    assert payload["model"] == "claude-sonnet-5"
    assert payload["max_tokens"] == 700
    assert "temperature" not in payload


def test_claude_feedback_request_omits_deprecated_temperature(monkeypatch):
    calls = []

    class FakeClaudeResponse:
        status_code = 200
        text = ""

        def json(self):
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                            '{"insights":["Overall Summary: Claude feedback works."],'
                            '"annotations":[]}'
                        ),
                    }
                ]
            }

    def fake_post(url, headers, json, timeout):
        calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return FakeClaudeResponse()

    monkeypatch.setattr("ai_feedback.integration.requests.post", fake_post)

    parsed, new_insights = get_structured_feedback_from_claude(
        api_key="claude-key",
        prompt="Return JSON feedback.",
        model="claude-sonnet-5",
        temperature=0.5,
        past_insights=[],
    )

    assert calls[0]["url"] == "https://api.anthropic.com/v1/messages"
    assert calls[0]["json"]["model"] == "claude-sonnet-5"
    assert "temperature" not in calls[0]["json"]
    assert "error" not in parsed
    assert new_insights == ["Overall Summary: Claude feedback works."]


@pytest.mark.parametrize(
    ("provider", "course_key_attr", "expects_client"),
    [
        ("openai", "openai_api_key", True),
        ("gemini", "gemini_api_key", False),
        ("claude", "claude_api_key", False),
    ],
)
def test_get_provider_credentials_uses_assignment_key_for_custom_provider(
    monkeypatch,
    provider,
    course_key_attr,
    expects_client,
):
    course = SimpleNamespace(**{course_key_attr: ""})
    assignment = SimpleNamespace(
        use_course_ai_default=False,
        ai_feedback_api_key=f"encrypted-assignment-{provider}-key",
    )
    fake_client = object()

    monkeypatch.setattr(
        "ai_feedback.integration.decrypt_api_key",
        lambda encrypted_key: {
            f"encrypted-assignment-{provider}-key": f"assignment-{provider}-key",
        }[encrypted_key],
    )
    monkeypatch.setattr(
        "ai_feedback.integration.OpenAI",
        lambda api_key: fake_client,
    )

    api_key, client = get_provider_credentials(provider, course, assignment)

    assert api_key == f"assignment-{provider}-key"
    if expects_client:
        assert client is fake_client
    else:
        assert client is None


def test_get_provider_credentials_rejects_assignment_key_for_different_provider(
    monkeypatch,
):
    course = SimpleNamespace(gemini_api_key="encrypted-course-gemini-key")
    assignment = SimpleNamespace(
        use_course_ai_default=False,
        ai_feedback_api_key="encrypted-openai-assignment-key",
    )

    monkeypatch.setattr(
        "ai_feedback.integration.decrypt_api_key",
        lambda encrypted_key: {
            "encrypted-openai-assignment-key": "sk-proj-openai-key",
            "encrypted-course-gemini-key": "AIza-gemini-key",
        }[encrypted_key],
    )

    with pytest.raises(
        ValueError,
        match="Assignment API key appears to be for OpenAI",
    ):
        get_provider_credentials("gemini", course, assignment)


@pytest.mark.parametrize(
    ("provider", "course_key_attr", "expects_client"),
    [
        ("openai", "openai_api_key", True),
        ("gemini", "gemini_api_key", False),
        ("claude", "claude_api_key", False),
    ],
)
def test_get_provider_credentials_falls_back_to_course_key_for_custom_provider(
    monkeypatch,
    provider,
    course_key_attr,
    expects_client,
):
    course = SimpleNamespace(**{course_key_attr: f"encrypted-course-{provider}-key"})
    assignment = SimpleNamespace(
        use_course_ai_default=False,
        ai_feedback_api_key="",
    )
    fake_client = object()

    monkeypatch.setattr(
        "ai_feedback.integration.decrypt_api_key",
        lambda encrypted_key: {
            f"encrypted-course-{provider}-key": f"course-{provider}-key",
        }[encrypted_key],
    )
    monkeypatch.setattr(
        "ai_feedback.integration.OpenAI",
        lambda api_key: fake_client,
    )

    api_key, client = get_provider_credentials(provider, course, assignment)

    assert api_key == f"course-{provider}-key"
    if expects_client:
        assert client is fake_client
    else:
        assert client is None


@pytest.mark.parametrize(
    ("provider", "course_key_attr", "expects_client"),
    [
        ("openai", "openai_api_key", True),
        ("gemini", "gemini_api_key", False),
        ("claude", "claude_api_key", False),
    ],
)
def test_get_provider_credentials_ignores_assignment_key_when_using_course_default(
    monkeypatch,
    provider,
    course_key_attr,
    expects_client,
):
    course = SimpleNamespace(**{course_key_attr: f"encrypted-course-{provider}-key"})
    assignment = SimpleNamespace(
        use_course_ai_default=True,
        ai_feedback_api_key=f"encrypted-assignment-{provider}-key",
    )
    fake_client = object()

    monkeypatch.setattr(
        "ai_feedback.integration.decrypt_api_key",
        lambda encrypted_key: {
            f"encrypted-course-{provider}-key": f"course-{provider}-key",
        }[encrypted_key],
    )
    monkeypatch.setattr(
        "ai_feedback.integration.OpenAI",
        lambda api_key: fake_client,
    )

    api_key, client = get_provider_credentials(provider, course, assignment)

    assert api_key == f"course-{provider}-key"
    if expects_client:
        assert client is fake_client
    else:
        assert client is None


@pytest.mark.parametrize(
    ("provider", "course_key_attr", "provider_label"),
    [
        ("openai", "openai_api_key", "OpenAI"),
        ("gemini", "gemini_api_key", "Gemini"),
        ("claude", "claude_api_key", "Claude"),
    ],
)
def test_get_provider_credentials_requires_saved_provider_key(
    provider,
    course_key_attr,
    provider_label,
):
    course = SimpleNamespace(**{course_key_attr: ""})
    assignment = SimpleNamespace(
        use_course_ai_default=False,
        ai_feedback_api_key="",
    )

    with pytest.raises(ValueError, match=f"Missing {provider_label} API key"):
        get_provider_credentials(provider, course, assignment)
