import copy
import json
import re

from util.encryption_utils import encrypt_api_key


LEGACY_FEEDBACK_PROMPT_ID = "legacy_feedback_prompt"
MAX_AI_FEEDBACK_REQUESTS = 1000

DEFAULT_AI_ALLOWED_INPUTS = {
    "assignment_description": True,
    "student_code": True,
    "test_results": True,
    "test_cases": False,
    "student_output": True,
}

DEFAULT_AI_FEEDBACK_PROMPTS = [
    {
        "id": "check_correctness",
        "title": "Check correctness",
        "prompt": (
            "Check whether the submission appears correct based on the assignment "
            "requirements and available test results. Give concise guidance without "
            "revealing the full solution."
        ),
        "enabled": True,
    },
    {
        "id": "debug_failed_tests",
        "title": "Debug failed tests",
        "prompt": (
            "Analyze failed test results and give debugging guidance. Point the "
            "student toward likely causes without giving copy-paste fixes."
        ),
        "enabled": True,
    },
    {
        "id": "review_edge_cases",
        "title": "Review edge cases",
        "prompt": (
            "Review the submission for important edge cases and boundary conditions "
            "that may not be fully covered by the visible tests."
        ),
        "enabled": True,
    },
    {
        "id": "explain_runtime_errors",
        "title": "Explain runtime errors",
        "prompt": (
            "Explain any runtime errors or exceptions in student-friendly language "
            "and suggest what part of the code to inspect."
        ),
        "enabled": True,
    },
    {
        "id": "review_code_style",
        "title": "Review code style",
        "prompt": (
            "Review code organization, readability, and maintainability only when "
            "those observations help the student improve the solution safely."
        ),
        "enabled": True,
    },
    {
        "id": "suggest_algorithmic_improvements",
        "title": "Suggest algorithmic improvements",
        "prompt": (
            "Suggest high-level algorithmic improvements or complexity concerns "
            "without rewriting the student's solution."
        ),
        "enabled": True,
    },
    {
        "id": "check_code_syntax",
        "title": "Check code syntax",
        "prompt": (
            "Review the student's code for syntax errors, Python best practices, "
            "and language-specific issues. Point out problematic patterns and suggest "
            "what to fix without rewriting the code."
        ),
        "enabled": True,
    },
    {
        "id": "compare_to_optimal_solution",
        "title": "Compare to optimal solution",
        "prompt": (
            "You are comparing the student's code against an optimal reference solution. "
            "First, analyze the assignment description to understand what the problem requires. "
            "Then generate an optimal approach internally and compare it to the student's code. "
            "Identify algorithmic differences, time/space complexity gaps, and structural improvements. "
            "Give feedback on how the student's approach differs from the optimal one without "
            "revealing the full reference solution. Focus on algorithmic thinking and design patterns."
        ),
        "enabled": True,
    },
    {
        "id": "personalized_feedback",
        "title": "Personalized feedback",
        "prompt": (
            "Based on this student's history and current submission, provide personalized feedback. "
            "Reference patterns from their previous work where relevant. "
            "Focus on areas where this specific student tends to struggle and give targeted guidance. "
            "Encourage growth and acknowledge improvements from past submissions."
        ),
        "enabled": True,
    },
]

AI_FEEDBACK_SETTING_KEYS = {
    "feedback_prompts",
    "allowed_inputs",
    "ai_feedback_prompts",
    "ai_allowed_inputs",
    "ai_feedback_enabled",
    "use_course_ai_default",
    "ai_feedback_provider",
    "ai_feedback_model",
    "ai_feedback_api_key",
    "ai_feedback_temperature",
    "ai_feedback_style",
    "ai_feedback_max_requests",
    "ai_feedback_wait_seconds",
}


def _copy_defaults(value):
    return copy.deepcopy(value)


def _decode_json_value(value):
    if value is None:
        return None

    if isinstance(value, bytes):
        value = value.decode("utf-8")

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None

        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return value

    return value


def _slugify(value, fallback):
    normalized = re.sub(r"[^a-z0-9]+", "_", (value or "").lower()).strip("_")
    return normalized or fallback


def _unique_prompt_id(prompt_id, title, index, seen_ids):
    base_id = _slugify(prompt_id or title, f"feedback_prompt_{index + 1}")
    candidate = base_id
    suffix = 2

    while candidate in seen_ids:
        candidate = f"{base_id}_{suffix}"
        suffix += 1

    seen_ids.add(candidate)
    return candidate


def split_ai_settings_payload(data):
    assignment_data = {}
    ai_settings_data = {}

    for key, value in (data or {}).items():
        if key in AI_FEEDBACK_SETTING_KEYS:
            ai_settings_data[key] = value
        else:
            assignment_data[key] = value

    return assignment_data, ai_settings_data


def normalize_feedback_prompts(value, legacy_prompt=None, validate=False):
    decoded_value = _decode_json_value(value)

    if decoded_value is None:
        legacy_prompt = (legacy_prompt or "").strip()
        if legacy_prompt:
            return [
                {
                    "id": LEGACY_FEEDBACK_PROMPT_ID,
                    "title": "Custom Feedback",
                    "prompt": legacy_prompt,
                    "enabled": True,
                }
            ]

        return _copy_defaults(DEFAULT_AI_FEEDBACK_PROMPTS)

    if not isinstance(decoded_value, list):
        if validate:
            raise ValueError("Feedback prompts must be a list")
        return _copy_defaults(DEFAULT_AI_FEEDBACK_PROMPTS)

    normalized_prompts = []
    seen_ids = set()

    for index, prompt_config in enumerate(decoded_value):
        if not isinstance(prompt_config, dict):
            if validate:
                raise ValueError("Each feedback prompt must be an object")
            continue

        title = str(prompt_config.get("title") or "").strip()
        prompt_text = str(
            prompt_config.get("prompt")
            or prompt_config.get("instruction")
            or ""
        ).strip()

        if validate and not title:
            raise ValueError("Prompt title is required")

        if validate and not prompt_text:
            raise ValueError("Prompt instruction text is required")

        if not title or not prompt_text:
            continue

        normalized_prompts.append(
            {
                "id": _unique_prompt_id(
                    str(prompt_config.get("id") or ""),
                    title,
                    index,
                    seen_ids,
                ),
                "title": title,
                "prompt": prompt_text,
                "enabled": bool(prompt_config.get("enabled", True)),
            }
        )

    return normalized_prompts


def normalize_allowed_inputs(value, validate=False):
    decoded_value = _decode_json_value(value)
    normalized_inputs = _copy_defaults(DEFAULT_AI_ALLOWED_INPUTS)

    if decoded_value is None:
        return normalized_inputs

    if not isinstance(decoded_value, dict):
        if validate:
            raise ValueError("Allowed inputs must be an object")
        return normalized_inputs

    for key in DEFAULT_AI_ALLOWED_INPUTS:
        if key not in decoded_value:
            continue

        if validate and not isinstance(decoded_value[key], bool):
            raise ValueError(f"Allowed input '{key}' must be a boolean")

        if isinstance(decoded_value[key], bool):
            normalized_inputs[key] = decoded_value[key]

    return normalized_inputs


def normalize_non_negative_int(
    value,
    field_name,
    allow_null=False,
    max_value=None,
):
    if value is None and allow_null:
        return None

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be a non-negative integer")

    if value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")

    if max_value is not None and value > max_value:
        raise ValueError(f"{field_name} must be less than or equal to {max_value}")

    return value


def serialize_assignment_ai_settings(assignment):
    feedback_prompts = normalize_feedback_prompts(
        getattr(assignment, "ai_feedback_prompts", None),
        legacy_prompt=getattr(assignment, "ai_feedback_prompt", None),
    )
    allowed_inputs = normalize_allowed_inputs(
        getattr(assignment, "ai_allowed_inputs", None)
    )

    return {
        "ai_feedback_enabled": bool(
            getattr(assignment, "ai_feedback_enabled", False)
        ),
        "use_course_ai_default": getattr(
            assignment,
            "use_course_ai_default",
            True,
        ) is not False,
        "ai_feedback_provider": getattr(assignment, "ai_feedback_provider", None),
        "ai_feedback_model": getattr(assignment, "ai_feedback_model", None),
        "has_assignment_ai_key": bool(
            getattr(assignment, "ai_feedback_api_key", None)
        ),
        "ai_feedback_temperature": getattr(
            assignment,
            "ai_feedback_temperature",
            None,
        ),
        "ai_feedback_style": getattr(assignment, "ai_feedback_style", None),
        "ai_feedback_max_requests": getattr(
            assignment,
            "ai_feedback_max_requests",
            None,
        ),
        "ai_feedback_wait_seconds": getattr(
            assignment,
            "ai_feedback_wait_seconds",
            None,
        ) or 0,
        "ai_feedback_prompts": feedback_prompts,
        "ai_allowed_inputs": allowed_inputs,
    }


def update_assignment_ai_settings(assignment, data):
    if "feedback_prompts" in data or "ai_feedback_prompts" in data:
        feedback_prompts = normalize_feedback_prompts(
            data.get("feedback_prompts", data.get("ai_feedback_prompts")),
            validate=True,
        )
        assignment.ai_feedback_prompts = feedback_prompts

        first_enabled_prompt = next(
            (prompt for prompt in feedback_prompts if prompt["enabled"]),
            feedback_prompts[0] if feedback_prompts else None,
        )
        assignment.ai_feedback_prompt = (
            first_enabled_prompt["prompt"] if first_enabled_prompt else None
        )

    if "allowed_inputs" in data or "ai_allowed_inputs" in data:
        assignment.ai_allowed_inputs = normalize_allowed_inputs(
            data.get("allowed_inputs", data.get("ai_allowed_inputs")),
            validate=True,
        )

    if "ai_feedback_enabled" in data:
        assignment.ai_feedback_enabled = bool(data["ai_feedback_enabled"])

    if "use_course_ai_default" in data:
        assignment.use_course_ai_default = data["use_course_ai_default"] is not False

    previous_provider = getattr(assignment, "ai_feedback_provider", None)

    if assignment.use_course_ai_default:
        assignment.ai_feedback_provider = None
        assignment.ai_feedback_model = None
        if hasattr(assignment, "ai_feedback_api_key"):
            assignment.ai_feedback_api_key = ""
    else:
        provider_changed = (
            "ai_feedback_provider" in data
            and data["ai_feedback_provider"] != previous_provider
        )
        if "ai_feedback_provider" in data:
            assignment.ai_feedback_provider = data["ai_feedback_provider"]
        if "ai_feedback_model" in data:
            assignment.ai_feedback_model = data["ai_feedback_model"]
        if "ai_feedback_api_key" in data:
            credential = str(data.get("ai_feedback_api_key") or "").strip()
            if credential:
                assignment.ai_feedback_api_key = encrypt_api_key(credential)
            elif provider_changed and hasattr(assignment, "ai_feedback_api_key"):
                assignment.ai_feedback_api_key = ""
        elif provider_changed and hasattr(assignment, "ai_feedback_api_key"):
            assignment.ai_feedback_api_key = ""

    if "ai_feedback_style" in data:
        assignment.ai_feedback_style = data["ai_feedback_style"]

    if "ai_feedback_max_requests" in data:
        assignment.ai_feedback_max_requests = normalize_non_negative_int(
            data.get("ai_feedback_max_requests"),
            "ai_feedback_max_requests",
            allow_null=True,
            max_value=MAX_AI_FEEDBACK_REQUESTS,
        )

    if "ai_feedback_wait_seconds" in data:
        assignment.ai_feedback_wait_seconds = normalize_non_negative_int(
            data.get("ai_feedback_wait_seconds"),
            "ai_feedback_wait_seconds",
        )

    if "ai_feedback_temperature" in data:
        temperature = data["ai_feedback_temperature"]
        if temperature in ("", None):
            assignment.ai_feedback_temperature = None
        else:
            try:
                temperature_value = float(temperature)
            except (TypeError, ValueError):
                raise ValueError("Invalid AI feedback temperature")

            if temperature_value < 0 or temperature_value > 1:
                raise ValueError("AI feedback temperature must be between 0 and 1")

            assignment.ai_feedback_temperature = temperature_value


def get_enabled_feedback_prompt(assignment, prompt_id=None):
    prompts = normalize_feedback_prompts(
        getattr(assignment, "ai_feedback_prompts", None),
        legacy_prompt=getattr(assignment, "ai_feedback_prompt", None),
    )

    if prompt_id:
        for prompt in prompts:
            if prompt["id"] != prompt_id:
                continue

            if prompt["enabled"]:
                return prompt

            raise ValueError("Selected AI feedback prompt is not enabled")

        raise ValueError("Selected AI feedback prompt was not found or is not enabled")

    for prompt in prompts:
        if prompt["enabled"]:
            return prompt

    raise ValueError("No AI feedback prompts are enabled for this assignment")


def _assignment_description(assignment):
    description = str(getattr(assignment, "description", "") or "").strip()
    if description:
        return description

    name = str(getattr(assignment, "name", "") or "").strip()
    if name:
        return f"Assignment: {name}"

    return ""


def _prepare_results_for_prompt(results, allowed_inputs):
    decoded_results = _decode_json_value(results)

    if not isinstance(decoded_results, dict):
        return decoded_results

    prepared_results = {}

    for key in ("score", "max_score", "execution_time", "visibility"):
        if key in decoded_results:
            prepared_results[key] = decoded_results[key]

    if allowed_inputs["student_output"]:
        for key in ("output", "stdout", "stderr", "programOutput"):
            if key in decoded_results:
                prepared_results[key] = decoded_results[key]

    tests = decoded_results.get("tests")
    if isinstance(tests, list):
        prepared_tests = []
        for test in tests:
            if not isinstance(test, dict):
                continue

            prepared_test = {}
            for key in ("name", "status", "score", "max_score", "visibility"):
                if key in test:
                    prepared_test[key] = test[key]

            if allowed_inputs["test_cases"]:
                for key in ("input", "input_data", "expected", "expected_output"):
                    if key in test:
                        prepared_test[key] = test[key]

            if allowed_inputs["student_output"]:
                for key in ("output", "stdout", "stderr", "actual_output"):
                    if key in test:
                        prepared_test[key] = test[key]

            prepared_tests.append(prepared_test)

        prepared_results["tests"] = prepared_tests

    return prepared_results


def _format_context_value(value):
    if value is None:
        return ""

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    if isinstance(value, (dict, list)):
        return json.dumps(value, indent=2, sort_keys=True)

    return str(value)


def build_allowed_feedback_context(
    assignment,
    code_text=None,
    autograder_results=None,
    test_cases=None,
    student_output=None,
):
    allowed_inputs = normalize_allowed_inputs(
        getattr(assignment, "ai_allowed_inputs", None)
    )
    context = {}

    if allowed_inputs["assignment_description"]:
        description = _assignment_description(assignment)
        if description:
            context["assignment_description"] = description

    if allowed_inputs["student_code"] and code_text:
        context["student_code"] = _format_context_value(code_text)

    if allowed_inputs["test_results"] and autograder_results:
        prepared_results = _prepare_results_for_prompt(
            autograder_results,
            allowed_inputs,
        )
        context["test_results"] = _format_context_value(prepared_results)

    if allowed_inputs["test_cases"] and test_cases:
        context["test_cases"] = _format_context_value(_decode_json_value(test_cases))

    if allowed_inputs["student_output"] and student_output:
        context["student_output"] = _format_context_value(student_output)

    return context


def render_feedback_context(context):
    if not context:
        return "No instructor-approved assignment or submission context is available."

    section_titles = {
        "assignment_description": "Assignment description",
        "student_code": "Student code",
        "test_results": "Autograder results",
        "test_cases": "Test cases",
        "student_output": "Student output",
    }

    rendered_sections = []
    for key, value in context.items():
        title = section_titles.get(key, key.replace("_", " ").title())
        rendered_sections.append(f"{title}:\n{value}")

    return "\n\n".join(rendered_sections)


def check_feedback_limits(assignment, student_id):
    """Check whether a student can request AI feedback for this assignment.

    Returns a dict with:
      allowed: bool
      remaining: int or None (None = unlimited)
      wait_seconds: int (seconds remaining before next request, 0 = ready)
      message: str (human-readable reason when not allowed)
    """
    max_requests = getattr(assignment, "ai_feedback_max_requests", None)
    wait_seconds = getattr(assignment, "ai_feedback_wait_seconds", 0) or 0

    from api.models import AIFeedbackRequest
    from api import db
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    # Count existing requests
    request_count = (
        db.session.query(AIFeedbackRequest)
        .filter_by(student_id=student_id, assignment_id=assignment.id)
        .count()
    )

    # Check max requests
    if max_requests is not None and max_requests == 0:
        return {
            "allowed": False,
            "remaining": 0,
            "wait_seconds": 0,
            "message": "AI feedback is disabled for this assignment.",
        }

    remaining = None
    if max_requests is not None:
        remaining = max(0, max_requests - request_count)
        if remaining <= 0:
            return {
                "allowed": False,
                "remaining": 0,
                "wait_seconds": 0,
                "message": "You have used all your AI feedback requests for this assignment.",
            }

    # Check wait time
    if wait_seconds > 0 and request_count > 0:
        last_request = (
            db.session.query(AIFeedbackRequest)
            .filter_by(student_id=student_id, assignment_id=assignment.id)
            .order_by(AIFeedbackRequest.created_at.desc())
            .first()
        )
        if last_request:
            elapsed = (now - last_request.created_at).total_seconds()
            if elapsed < wait_seconds:
                remaining_wait = int(wait_seconds - elapsed)
                return {
                    "allowed": False,
                    "remaining": remaining,
                    "wait_seconds": remaining_wait,
                    "message": f"Please wait {remaining_wait} seconds before requesting AI feedback again.",
                }

    return {
        "allowed": True,
        "remaining": remaining,
        "wait_seconds": 0,
        "message": "",
    }


def record_feedback_request(student_id, assignment_id, prompt_id=None):
    """Record an AI feedback request in the database."""
    import uuid
    from datetime import datetime, timezone
    from api.models import AIFeedbackRequest
    from api import db

    request_record = AIFeedbackRequest(
        id=str(uuid.uuid4()),
        student_id=student_id,
        assignment_id=assignment_id,
        prompt_id=prompt_id,
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(request_record)
    db.session.commit()


def get_student_feedback_status(assignment, student_id):
    """Get the student's current feedback request status for this assignment."""
    max_requests = getattr(assignment, "ai_feedback_max_requests", None)
    wait_seconds = getattr(assignment, "ai_feedback_wait_seconds", 0) or 0

    from api.models import AIFeedbackRequest
    from api import db
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)

    request_count = (
        db.session.query(AIFeedbackRequest)
        .filter_by(student_id=student_id, assignment_id=assignment.id)
        .count()
    )

    remaining = None
    if max_requests is not None:
        remaining = max(0, max_requests - request_count)

    wait_remaining = 0
    if wait_seconds > 0 and request_count > 0:
        last_request = (
            db.session.query(AIFeedbackRequest)
            .filter_by(student_id=student_id, assignment_id=assignment.id)
            .order_by(AIFeedbackRequest.created_at.desc())
            .first()
        )
        if last_request:
            elapsed = (now - last_request.created_at).total_seconds()
            if elapsed < wait_seconds:
                wait_remaining = int(wait_seconds - elapsed)

    return {
        "remaining": remaining,
        "wait_seconds": wait_remaining,
        "max_requests": max_requests,
        "total_requests": request_count,
    }


def get_chat_history(student_id, assignment_id, limit=20):
    """Retrieve recent chat messages for a student's assignment."""
    from api.models import AIChatMessage
    from api import db

    messages = (
        db.session.query(AIChatMessage)
        .filter_by(student_id=student_id, assignment_id=assignment_id)
        .order_by(AIChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )

    # Reverse to get chronological order
    messages.reverse()

    return [{"role": msg.role, "content": msg.content} for msg in messages]


def store_chat_message(student_id, assignment_id, role, content, prompt_id=None):
    """Store a chat message in the database for AI memory."""
    import uuid
    from datetime import datetime, timezone
    from api.models import AIChatMessage
    from api import db

    message = AIChatMessage(
        id=str(uuid.uuid4()),
        student_id=student_id,
        assignment_id=assignment_id,
        role=role,
        content=content,
        prompt_id=prompt_id,
        created_at=datetime.now(timezone.utc),
    )
    db.session.add(message)
    db.session.commit()
