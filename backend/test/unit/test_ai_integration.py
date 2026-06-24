from ai_integration import (
    DEFAULT_FEEDBACK_PROMPT,
    RETURN_SPEC,
    build_feedback_prompt,
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

    monkeypatch.setattr("ai_integration.requests.post", fake_post)

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
