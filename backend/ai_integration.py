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


DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.5
CORRECTNESS_SYSTEM_PROMPT = (
    "You are an AI feedback assistant for programming assignments. "
    "Give short, student-facing correctness and debugging hints only. "
    "Do not comment on style, formatting, naming, indentation, readability, "
    "organization, refactoring, or general best practices. "
    "Do not provide corrected code, copy-paste fixes, or the full solution. "
    "Return only valid JSON."
)
DEFAULT_FEEDBACK_PROMPT = """
You are giving short, student-facing feedback on a programming assignment.

Your job is to help the student debug correctness problems without revealing the solution.

Only give feedback that is directly related to whether the submitted program meets the assignment requirements or passes the tests.

Allowed feedback topics:
- Incorrect logic
- Missing required behavior
- Failed test cases
- Edge cases
- Runtime errors
- Infinite loops
- Incorrect input or output handling
- Incorrect return values
- Incorrect state updates
- Incorrect use of required algorithmic steps
- Performance only if it causes timeout or failed tests

Forbidden feedback topics:
- Style
- Formatting
- Naming
- Indentation
- Readability
- Code organization
- Refactoring
- General best practices that do not affect correctness

Rules:
- Do not provide corrected code.
- Do not give copy-paste fixes.
- Do not reveal the final answer.
- Do not explain how to fully solve the assignment.
- Give hints that help the student investigate the bug.
- Prefer comments tied to specific code patterns or failed behavior.
- If the issue is based on test output, mention the symptom but not the full fix.
- Keep each comment under 2 sentences.
- If there are no clear correctness issues, return one insight saying no correctness issue is obvious from the available information.

Return strictly valid JSON in this format:
{
  "insights": [
    "One short overall takeaway about the main correctness issue or debugging direction."
  ],
  "annotations": [
    {
      "pattern": "exact code snippet or recognizable code pattern from the student code",
      "comment": "A short correctness-focused hint that helps the student debug without giving the answer."
    }
  ]
}
"""

RETURN_SPEC = """
Return only valid JSON. Do not use markdown, code fences, bullet points, or extra explanation.

Use this exact JSON structure:
{
  "insights": [
    "One short overall takeaway about the main correctness issue or debugging direction."
  ],
  "annotations": [
    {
      "pattern": "exact code snippet or recognizable code pattern from the student code",
      "comment": "A short correctness-focused hint that helps the student debug without giving the answer."
    }
  ]
}

Strict rules:
- Do not provide corrected code.
- Do not give copy-paste fixes.
- Do not reveal the final answer.
- Do not comment on style, formatting, naming, indentation, readability, organization, or refactoring.
- Do not make efficiency suggestions unless the submitted code times out or fails because of performance.
- Only discuss correctness, logic, required behavior, edge cases, runtime errors, failed tests, input/output handling, or algorithmic mistakes.
- Every annotation must connect to a concrete code pattern or observable failed behavior.
- Keep each comment under 2 sentences.
- If there are no clear correctness issues, return:
{
  "insights": [
    "No clear correctness issue is obvious from the available code and test results."
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
):
    """Constructs the full prompt sent to the AI model."""
    return (
        f"{base_prompt or DEFAULT_FEEDBACK_PROMPT}\n\n"
        f"{style_instruction}\n\n"
        f"{RETURN_SPEC}\n\n"
        "Past student insights:\n"
        f"{past_insights}\n\n"
        "Student code:\n"
        f"{code}\n\n"
        "Autograder results:\n"
        f"{autograder_results}\n\n"
    )


def clean_ai_response(text):
    """Strips markdown formatting and unescapes newlines."""
    if not text:
        return ""

    lines = text.splitlines()

    if lines and lines[0].startswith("```"):
        lines = lines[1:]

    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    cleaned = "\n".join(lines).strip()
    return cleaned.replace("\\n", "\n")


def parse_feedback_json(raw_response, provider_name, past_insights):
    """Parses model output into JSON feedback."""
    cleaned = clean_ai_response(raw_response)

    try:
        parsed_json = json.loads(cleaned)

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
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 700,
                "responseMimeType": "application/json",
            },
        },
        timeout=30,
    )

    if response.status_code >= 400:
        raise ValueError(f"Gemini API error: {response.text}")

    data = response.json()
    raw_response = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
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

        custom_prompt = (assignment.ai_feedback_prompt or "").strip()
        base_prompt = custom_prompt if custom_prompt else DEFAULT_FEEDBACK_PROMPT
        style_instruction = get_feedback_style_instruction(assignment, course)

        provider, model = get_provider_and_model(assignment, course)
        temperature = get_temperature(assignment, course)
        api_key, client = get_provider_credentials(provider, course)

        print(
            f"AI_FEEDBACK: Using provider={provider}, model={model}, temperature={temperature}",
            flush=True,
        )

        prompt = build_feedback_prompt(
            base_prompt,
            past_insights,
            code_text,
            results_json_content,
            style_instruction,
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