import os
from openai import OpenAI
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from util.errors import InternalProcessingError, NotFoundError
from api.models import Assignment, Submission, User, Course
from api import db

import subprocess
import os
import hashlib
import docker 
import zipfile
import shutil
import time
from dotenv import load_dotenv
from openai import OpenAI
import threading
from sqlalchemy.orm import aliased
import json

from util.encryption_utils import decrypt_api_key


DEFAULT_MODEL="gpt-4-turbo"
DEFAULT_FEEDBACK_PROMPT="You are an AI used to provide constructive feedback to students on their coding assignments.\
    Provide feedback on the following assignment regarding correctness, efficiency, code quality, documentation,\
    error handling, style/formatting.\n"
DEFAULT_TEMPERATURE=0.5
RETURN_SPEC="Response should be JSON in the form:\
            { 'insights': <updated insights for this student's coding behavior, focused on areas of improvement. Should be a series of consise bullets>,\
            'annotations': [{'pattern': <> , 'comment': <>}, ...]\
            }"

# Load environment variables
load_dotenv()

# Load encryption key for decrypting API key
SECRET_KEY = os.getenv("API_SECRET_KEY")
cipher = Fernet(SECRET_KEY) if SECRET_KEY else None

# --- helper functions for getting AI feedback ---

# Function to fetch related submission, assignment, course, and student records from DB
#  returns a tuple of (submission, assignment, course, student)
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
    else:
        raise ValueError(f"Submission ID {submission_id} not found")

def build_feedback_prompt(base_prompt, past_insights, code, autograder_results):
    """Constructs the full prompt sent to the AI model."""
    return (
        f"{base_prompt}"
        "Pay special attention to the past insights of this student:\n"
        f"{past_insights}"

        "Response should be strictly JSON, with no extra formatting, in the form:\n"
        "{ 'insights': [...], 'annotations': [{pattern: ..., comment: ...}, ...] }\n\n"
        "Code:\n\n"
        f"{code}\n\n"
        "Autograder results:\n\n"
        f"{autograder_results}\n\n"
    )

def format_message(text, model="gpt-4o"):
    """Formats messages depending on the OpenAI model being used."""
    if "gpt-4o" in model:
        return [{ "type": "text", "text": str(text) }]
    return text


def get_structured_feedback_from_openai(client, prompt, model, temperature, past_insights):
    """Sends request to OpenAI and parses JSON feedback."""
    response = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": format_message("You are an AI that provides constructive criticism on submitted code.", model)
            },
            {
                "role": "user",
                "content": format_message(prompt, model)
            }
        ],
        model=model,
        max_tokens=700,
        temperature=temperature,
        timeout=30  # timeout in seconds
    )

    raw_response = response.choices[0].message.content.strip()
    cleaned = clean_ai_response(raw_response)

    try:
        parsed_json = json.loads(cleaned)
        if isinstance(parsed_json, str):
            parsed_json = json.loads(parsed_json)

        print("AI_FEEDBACK:")
        print(json.dumps(parsed_json, indent=4))

        return parsed_json, parsed_json.get("insights", [])
    except Exception:
        print("AI_FEEDBACK: Failed to parse JSON from response.")
        return {
            "error": "Failed to parse OpenAI response as JSON",
            "response_text": cleaned
        }, past_insights


def clean_ai_response(text):
    """Strips markdown formatting and unescapes newlines."""
    lines = text.splitlines()

    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    cleaned = "\n".join(lines).strip()
    return cleaned.replace("\\n", "\n")


def update_submission_feedback(submission_id, ai_feedback_json, new_insights):
    """Updates the database with the AI feedback and new student insights."""
    submission = Submission.query.get(submission_id)
    student = User.query.get(submission.student_id)

    submission.ai_feedback = json.dumps(ai_feedback_json)
    student.coding_insights = str(new_insights)

    db.session.commit()



# Define a background task for obtaining and recording AI feedback.
def async_get_ai_feedback(app, submission_id, file_path, results_json_content):
    ctx = app.app_context()
    ctx.push()

    try:
        with open(file_path, 'r') as code_file:
            code_text = code_file.read()

        submission, assignment, course, student = fetch_submission_data(submission_id)

        if not assignment.ai_feedback_enabled:
            print(f"AI_FEEDBACK: Disabled for submission {submission_id}")
            return

        prompt = build_feedback_prompt(
            assignment.ai_feedback_prompt,
            student.coding_insights,
            code_text,
            results_json_content
        )

        model = assignment.ai_feedback_model
        temperature = assignment.ai_feedback_temperature

        decrypted_api_key = decrypt_api_key(course.openai_api_key)
        client = OpenAI(api_key=decrypted_api_key)

        ai_feedback_json, new_insights = get_structured_feedback_from_openai(
            client, prompt, model, temperature, student.coding_insights
        )

        update_submission_feedback(submission_id, ai_feedback_json, new_insights)

    except Exception as e:
        print(f"AI_FEEDBACK: Unexpected error - {e}")

    finally:
        ctx.pop()