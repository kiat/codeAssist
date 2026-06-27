import os
import subprocess
import hashlib
import docker
import zipfile
import shutil
import time
import threading
import json
import requests

from openai import OpenAI
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from sqlalchemy.orm import aliased

from util.errors import InternalProcessingError, NotFoundError
from util.encryption_utils import decrypt_api_key
from api.models import Assignment, Submission, User, Course
from api import db
from ai_feedback.settings import (
    build_allowed_feedback_context,
    get_enabled_feedback_prompt,
    render_feedback_context,
)


DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.5
GEMINI_MAX_OUTPUT_TOKENS = 1600
CORRECTNESS_SYSTEM_PROMPT = (
    "You are an AI feedback assistant for programming assignments. "
    "Give short, student-facing feedback about correctness, test results, "
    "robustness, maintainability, and safe improvement opportunities. "
    "Do not provide corrected code, copy-paste fixes, or the full solution. "
    "Return only valid JSON."
)
DEFAULT_FEEDBACK_PROMPT = """
You are giving short, student-facing feedback on a programming assignment.

Your goal is to help the student understand their submission quality, correctness, and possible improvements without revealing the full solution.

Always provide useful feedback, even if the submitted code passes all visible tests.

Feedback should be professional, concise, and similar to feedback from a programming course autograder or Gradescope-style review.

Required feedback sections:
1. Overall Summary
   - Briefly summarize whether the submission appears correct based on the test results and available code.
   - If all tests pass, mention that no major correctness issue is obvious.

2. Correctness Feedback
   - Comment on failed tests, missing behavior, runtime errors, incorrect outputs, or edge cases.
   - If there are no failed tests, say that the implementation appears to satisfy the tested requirements.

3. Improvement Suggestions
   - Give safe suggestions about robustness, edge cases, maintainability, or clarity.
   - Suggestions should help the student improve without rewriting their code.

4. Line Comments
   - Add line-level comments only when a specific line or small code section is worth noting.
   - Line comments can point out possible bugs, fragile logic, edge case risks, or useful improvements.
   - Use a single-line code pattern for each annotation. Do not include newline characters in the pattern value.
   - Do not force line comments if there is no meaningful line-specific feedback.

Allowed feedback topics:
- Incorrect logic
- Missing required behavior
- Failed test cases
- Edge cases
- Runtime errors
- Incorrect input/output handling
- Incorrect return values
- Algorithm mistakes
- Robustness concerns
- Maintainability concerns that could affect future correctness
- Clear improvement suggestions

Avoid:
- Nitpicky formatting feedback
- Pure style-only comments
- Personal criticism
- Rewriting the student's solution
- Giving copy-paste fixes
- Revealing the full answer

Rules:
- Keep the tone professional and encouraging.
- Do not provide corrected code.
- Do not give copy-paste fixes.
- Do not reveal the final answer.
- Keep each comment short and specific.
- If all tests pass, still provide an overall summary and at least one improvement or robustness suggestion when possible.
- If no meaningful improvement is visible, say the submission appears solid based on the available tests.

Return strictly valid JSON in this format:
{
  "insights": [
    "Overall Summary: A short summary of the submission based on the code and tests.",
    "Correctness Feedback: A short correctness-focused observation.",
    "Improvement Suggestion: A safe suggestion about robustness, edge cases, maintainability, or clarity."
  ],
  "annotations": [
    {
      "pattern": "exact code snippet or recognizable code pattern from the student code",
      "comment": "A short line-specific comment when a concrete code pattern is worth noting."
    }
  ]
}
"""

RETURN_SPEC = """
Return only valid JSON. Do not use markdown, code fences, bullet points, or extra explanation.

Use this exact JSON structure:
{
  "insights": [
    "Overall Summary: A short summary of the submission based on the code and tests.",
    "Correctness Feedback: A short correctness-focused observation.",
    "Improvement Suggestion: A safe suggestion about robustness, edge cases, maintainability, or clarity."
  ],
  "annotations": [
    {
      "pattern": "exact code snippet or recognizable code pattern from the student code",
      "comment": "A short line-specific comment when a concrete code pattern is worth noting."
    }
  ]
}

Strict rules:
- Include general insights for every submission.
- Include annotations only when line-specific feedback is helpful.
- Use a single-line code pattern for each annotation. Do not include newline characters in the pattern value.
- Do not provide corrected code.
- Do not give copy-paste fixes.
- Do not reveal the final answer.
- Keep each comment short and specific.
- Discuss correctness, logic, required behavior, edge cases, runtime errors, failed tests, input/output handling, algorithmic mistakes, robustness, maintainability, or clarity.
- Every annotation must connect to a concrete code pattern, observable failed behavior, edge case risk, or meaningful improvement opportunity.
- Avoid nitpicky formatting feedback and pure style-only comments.
- If there are no clear correctness issues, still return useful general insights, for example:
{
  "insights": [
    "Overall Summary: No clear correctness issue is obvious from the available code and test results.",
    "Correctness Feedback: The implementation appears to satisfy the tested requirements.",
    "Improvement Suggestion: Consider whether additional edge cases should be handled gracefully."
  ],
  "annotations": []
}
"""

load_dotenv()

SECRET_KEY = os.getenv("API_SECRET_KEY")
cipher = Fernet(SECRET_KEY) if SECRET_KEY else None


def fetch_submission_data(submission_id):
    """Fetch related submission, assignment, course, and student records from DB."""
    assignment_alias = aliased(Assignment)
    course_alias = aliased(Course)
    student_alias = aliased(User)

    result = (
        db.session.query(Submission, assignment_alias, course_alias, student_alias)
        .join(assignment_alias, Submission.assignment_id == assignment_alias.id)
        .join(course_alias, assignment_alias.course_id == course_alias.id)
        .join(student_alias, Submission.student_id == student_alias.id)
        .filter(Submission.id == submission_id)
        .first()
    )

    if result:
        return result

    raise ValueError(f"Submission ID {submission_id} not found")
def get_feedback_style_instruction(assignment, course):
    """Return prompt instruction based on selected feedback style."""
    style = (
        getattr(assignment, "ai_feedback_style", None)
        or getattr(course, "default_feedback_style", None)
        or "balanced"
    )

    style = style.lower()

    if style == "hint-based":
        return (
            "Feedback style: hint-based. Give indirect debugging hints or guiding questions. "
            "Do not identify the exact fix."
        )

    if style == "detailed-debugging":
        return (
            "Feedback style: detailed debugging. Give slightly more explanation about the likely correctness issue, "
            "what behavior to test, and what part of the code to inspect. Still do not provide corrected code."
        )

    return (
        "Feedback style: balanced. Give concise correctness-focused feedback with enough context to guide debugging."
    )

def build_feedback_prompt(
    base_prompt,
    past_insights,
    code,
    autograder_results,
    style_instruction,
    feedback_context=None,
):
    """Constructs the full prompt sent to the AI model."""
    if feedback_context is None:
        context_text = (
            "Student code:\n"
            f"{code}\n\n"
            "Autograder results:\n"
            f"{autograder_results}\n\n"
        )
    else:
        context_text = f"{render_feedback_context(feedback_context)}\n\n"

    return (
        f"{base_prompt or DEFAULT_FEEDBACK_PROMPT}\n\n"
        f"{style_instruction}\n\n"
        f"{RETURN_SPEC}\n\n"
        "Past student insights:\n"
        f"{past_insights}\n\n"
        f"{context_text}"
    )


def clean_ai_response(text):
    """Strips markdown formatting while preserving valid JSON escapes."""
    if not text:
        return ""

    lines = text.splitlines()

    if lines and lines[0].startswith("```"):
        lines = lines[1:]

    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines).strip()


def escape_control_chars_in_json_strings(text):
    """Escapes literal control characters that providers sometimes put in JSON strings."""
    result = []
    in_string = False
    escaped = False

    for char in text:
        if in_string:
            if escaped:
                result.append(char)
                escaped = False
            elif char == "\\":
                result.append(char)
                escaped = True
            elif char == '"':
                result.append(char)
                in_string = False
            elif char == "\n":
                result.append("\\n")
            elif char == "\r":
                result.append("\\r")
            elif char == "\t":
                result.append("\\t")
            elif ord(char) < 32:
                result.append(f"\\u{ord(char):04x}")
            else:
                result.append(char)
            continue

        result.append(char)
        if char == '"':
            in_string = True

    return "".join(result)


def decode_feedback_candidate(candidate):
    """Attempts to decode a JSON candidate, including repaired string controls."""
    decoder = json.JSONDecoder()

    for prepared_candidate in (
        candidate,
        escape_control_chars_in_json_strings(candidate),
    ):
        try:
            return json.loads(prepared_candidate)
        except json.JSONDecodeError:
            pass

        try:
            parsed_json, _ = decoder.raw_decode(prepared_candidate)
            return parsed_json
        except json.JSONDecodeError:
            pass

    raise json.JSONDecodeError("Unable to decode feedback JSON", candidate, 0)


def load_feedback_json(cleaned_response):
    """Loads JSON, tolerating provider wrappers and unescaped string line breaks."""
    try:
        return decode_feedback_candidate(cleaned_response)
    except json.JSONDecodeError:
        for index, char in enumerate(cleaned_response):
            if char not in "{[":
                continue

            try:
                return decode_feedback_candidate(cleaned_response[index:])
            except json.JSONDecodeError:
                continue

        raise


def parse_feedback_json(raw_response, provider_name, past_insights):
    """Parses model output into JSON feedback."""
    cleaned = clean_ai_response(raw_response)

    try:
        parsed_json = load_feedback_json(cleaned)

        if isinstance(parsed_json, str):
            parsed_json = json.loads(parsed_json)

        print("AI_FEEDBACK:")
        print(json.dumps(parsed_json, indent=4), flush=True)

        return parsed_json, parsed_json.get("insights", [])

    except Exception as e:
        print(
            f"AI_FEEDBACK: Failed to parse {provider_name} JSON response: {e}",
            flush=True,
        )
        print(f"AI_FEEDBACK RAW RESPONSE: {cleaned}", flush=True)

        return {
            "error": f"Failed to parse {provider_name} response as JSON",
            "response_text": cleaned,
        }, past_insights


def get_gemini_generation_config(model, temperature):
    """Builds Gemini generation settings for complete JSON feedback."""
    config = {
        "temperature": temperature,
        "maxOutputTokens": GEMINI_MAX_OUTPUT_TOKENS,
        "responseMimeType": "application/json",
    }

    model_id = (model or "").lower()
    if "gemini-2.5-flash" in model_id:
        config["thinkingConfig"] = {"thinkingBudget": 0}
    elif "gemini-2.5-pro" in model_id:
        config["thinkingConfig"] = {"thinkingBudget": 128}

    return config


def get_structured_feedback_from_openai(client, prompt, model, temperature, past_insights):
    """Sends request to OpenAI and parses JSON feedback."""
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": CORRECTNESS_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        model=model,
        max_tokens=700,
        temperature=temperature,
        timeout=30,
        response_format={"type": "json_object"},
    )

    raw_response = response.choices[0].message.content.strip()
    return parse_feedback_json(raw_response, "OpenAI", past_insights)


def get_structured_feedback_from_gemini(api_key, prompt, model, temperature, past_insights):
    """Sends request to Gemini and parses JSON feedback."""
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        params={"key": api_key},
        json={
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": f"{CORRECTNESS_SYSTEM_PROMPT}\n\n{prompt}"
                        }
                    ],
                }
            ],
            "generationConfig": get_gemini_generation_config(model, temperature),
        },
        timeout=30,
    )

    if response.status_code >= 400:
        raise ValueError(f"Gemini API error: {response.text}")

    data = response.json()
    candidate = data.get("candidates", [{}])[0]
    finish_reason = candidate.get("finishReason")
    if finish_reason:
        print(f"AI_FEEDBACK: Gemini finishReason={finish_reason}", flush=True)

    raw_response = "".join(
        part.get("text", "")
        for part in candidate.get("content", {}).get("parts", [])
        if not part.get("thought")
    )

    return parse_feedback_json(raw_response, "Gemini", past_insights)


def get_structured_feedback_from_claude(api_key, prompt, model, temperature, past_insights):
    """Sends request to Claude and parses JSON feedback."""
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": model,
            "max_tokens": 700,
            "temperature": temperature,
            "system": CORRECTNESS_SYSTEM_PROMPT,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        },
        timeout=30,
    )

    if response.status_code >= 400:
        raise ValueError(f"Claude API error: {response.text}")

    data = response.json()
    content = data.get("content", [])

    raw_response = ""
    if content and content[0].get("type") == "text":
        raw_response = content[0].get("text", "")

    return parse_feedback_json(raw_response, "Claude", past_insights)


def update_submission_feedback(submission_id, ai_feedback_json, new_insights):
    """Updates the database with the AI feedback and new student insights."""
    submission = Submission.query.get(submission_id)

    if not submission:
        raise ValueError(f"Submission ID {submission_id} not found")

    student = User.query.get(submission.student_id)

    if not student:
        raise ValueError(f"Student ID {submission.student_id} not found")

    submission.ai_feedback = json.dumps(ai_feedback_json)
    student.coding_insights = str(new_insights)

    db.session.commit()


def get_provider_and_model(assignment, course):
    """Chooses provider/model from course default or assignment override."""
    if getattr(assignment, "use_course_ai_default", True):
        provider = course.default_ai_provider or "openai"
        model = course.default_ai_model or DEFAULT_MODEL
    else:
        provider = (
            assignment.ai_feedback_provider
            or course.default_ai_provider
            or "openai"
        )
        model = (
            assignment.ai_feedback_model
            or course.default_ai_model
            or DEFAULT_MODEL
        )

    return provider, model


def get_temperature(assignment, course):
    """Chooses assignment temperature, course temperature, or default."""
    try:
        return float(
            assignment.ai_feedback_temperature
            or course.default_ai_temperature
            or DEFAULT_TEMPERATURE
        )
    except (TypeError, ValueError):
        return DEFAULT_TEMPERATURE


def get_provider_credentials(provider, course):
    """Returns API key and OpenAI client if needed."""
    api_key = None
    client = None

    if provider == "openai":
        if not course.openai_api_key:
            raise ValueError("Missing OpenAI API key for this course")

        api_key = decrypt_api_key(course.openai_api_key)
        client = OpenAI(api_key=api_key)

    elif provider == "gemini":
        if not course.gemini_api_key:
            raise ValueError("Missing Gemini API key for this course")

        api_key = decrypt_api_key(course.gemini_api_key)

    elif provider == "claude":
        if not course.claude_api_key:
            raise ValueError("Missing Claude API key for this course")

        api_key = decrypt_api_key(course.claude_api_key)

    else:
        raise ValueError(f"Unsupported AI provider: {provider}")

    return api_key, client


def get_feedback_by_provider(provider, api_key, client, prompt, model, temperature, past_insights):
    """Calls the selected AI provider."""
    if provider == "openai":
        return get_structured_feedback_from_openai(
            client,
            prompt,
            model,
            temperature,
            past_insights,
        )

    if provider == "gemini":
        return get_structured_feedback_from_gemini(
            api_key,
            prompt,
            model,
            temperature,
            past_insights,
        )

    if provider == "claude":
        return get_structured_feedback_from_claude(
            api_key,
            prompt,
            model,
            temperature,
            past_insights,
        )

    raise ValueError(f"Unsupported AI provider: {provider}")


def async_get_ai_feedback(app, submission_id, file_path, results_json_content):
    """Background task for obtaining and recording AI feedback."""
    ctx = app.app_context()
    ctx.push()

    try:
        print(f"AI_FEEDBACK: Starting for submission {submission_id}", flush=True)

        with open(file_path, "r") as code_file:
            code_text = code_file.read()

        print("AI_FEEDBACK: Code file loaded", flush=True)

        submission, assignment, course, student = fetch_submission_data(submission_id)

        print(
            f"AI_FEEDBACK: Loaded DB records. enabled={assignment.ai_feedback_enabled}",
            flush=True,
        )

        if not assignment.ai_feedback_enabled:
            print(f"AI_FEEDBACK: Disabled for submission {submission_id}", flush=True)
            return

        past_insights = student.coding_insights or "No prior insights."

        prompt_config = get_enabled_feedback_prompt(assignment)
        base_prompt = prompt_config.get("prompt") or DEFAULT_FEEDBACK_PROMPT
        style_instruction = get_feedback_style_instruction(assignment, course)

        provider, model = get_provider_and_model(assignment, course)
        temperature = get_temperature(assignment, course)
        api_key, client = get_provider_credentials(provider, course)

        print(
            f"AI_FEEDBACK: Using provider={provider}, model={model}, temperature={temperature}",
            flush=True,
        )

        feedback_context = build_allowed_feedback_context(
            assignment=assignment,
            code_text=code_text,
            autograder_results=results_json_content,
        )

        prompt = build_feedback_prompt(
            base_prompt,
            past_insights,
            code_text,
            results_json_content,
            style_instruction,
            feedback_context=feedback_context,
        )

        print(f"AI_FEEDBACK: Calling {provider}", flush=True)

        ai_feedback_json, new_insights = get_feedback_by_provider(
            provider,
            api_key,
            client,
            prompt,
            model,
            temperature,
            past_insights,
        )

        print("AI_FEEDBACK: Updating submission feedback", flush=True)

        update_submission_feedback(submission_id, ai_feedback_json, new_insights)

        print(f"AI_FEEDBACK: Saved feedback for submission {submission_id}", flush=True)

    except Exception as e:
        print(f"AI_FEEDBACK: Unexpected error - {type(e).__name__}: {e}", flush=True)

        try:
            submission = Submission.query.get(submission_id)

            if submission:
                submission.ai_feedback = json.dumps({
                    "error": f"AI feedback generation failed: {type(e).__name__}: {e}",
                    "insights": [
                        "AI feedback could not be generated for this submission. Please review the submission manually."
                    ],
                    "annotations": []
                })

                db.session.commit()

                print(
                    f"AI_FEEDBACK: Saved failure feedback for submission {submission_id}",
                    flush=True,
                )

        except Exception as save_error:
            db.session.rollback()
            print(
                f"AI_FEEDBACK: Failed to save error feedback - {type(save_error).__name__}: {save_error}",
                flush=True,
            )

    finally:
        ctx.pop()
