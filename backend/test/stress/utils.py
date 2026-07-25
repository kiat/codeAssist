import os
import uuid

import requests


BASE_URL = os.environ.get("STRESS_BASE_URL", "http://localhost:5001")


def raise_for_status_with_body(response, action):
    if response.status_code >= 400:
        print()
        print(f"{action} failed")
        print(f"Status code: {response.status_code}")
        print(f"Response body: {response.text}")
        print()

    response.raise_for_status()


def is_http_status(error, *status_codes):
    response = getattr(error, "response", None)
    return response is not None and response.status_code in status_codes


def create_assignment(name, course_id, **extra_fields):
    url = f"{BASE_URL}/create_assignment"
    payload = {
        "name": name,
        "course_id": course_id,
    }
    payload.update(extra_fields)

    response = requests.post(url, json=payload)

    if response.status_code >= 400:
        print("Create assignment payload:")
        print(payload)

    raise_for_status_with_body(response, "Create assignment")
    return response.json()["id"]


def create_course(name, instructor_id=None, **extra_fields):
    if instructor_id is None:
        instructor_id = add_user(
            name=f"stress_instructor_{uuid.uuid4().hex[:8]}",
            role="Instructor",
        )

    payload = {
        "name": name,
        "instructor_id": instructor_id,
        "semester": extra_fields.pop("semester", "Fall"),
        "year": extra_fields.pop("year", "2026"),
        "entryCode": extra_fields.pop("entryCode", f"STRESS{uuid.uuid4().hex[:10].upper()}"),
        "allowEntryCode": extra_fields.pop("allowEntryCode", True),
    }
    payload.update(extra_fields)

    response = requests.post(f"{BASE_URL}/create_course", json=payload)

    if response.status_code >= 400:
        print("Create course payload:")
        print(payload)

    raise_for_status_with_body(response, "Create course")
    return response.json()["id"]


def delete_course(course_id):
    if not course_id:
        return None

    response = requests.delete(
        f"{BASE_URL}/delete_course",
        params={"course_id": course_id},
    )
    raise_for_status_with_body(response, "Delete course")
    return response.json()


def get_course(course_id):
    response = requests.get(
        f"{BASE_URL}/get_course_info",
        params={"course_id": course_id},
    )
    raise_for_status_with_body(response, "Get course")
    data = response.json()
    if isinstance(data, list):
        return data[0] if data else None
    return data


def get_course_assignments(course_id):
    response = requests.get(
        f"{BASE_URL}/get_course_assignments",
        params={"course_id": course_id},
    )
    raise_for_status_with_body(response, "Get course assignments")
    data = response.json()
    if isinstance(data, dict):
        return data.get("assignments", [])
    return data


def get_assignment(assignment_id):
    response = requests.get(
        f"{BASE_URL}/get_assignment",
        params={"assignment_id": assignment_id},
    )
    raise_for_status_with_body(response, "Get assignment")
    return response.json()


def create_enrollment(student_id, course_id, role="student"):
    response = requests.post(
        f"{BASE_URL}/create_enrollment",
        json={
            "student_id": student_id,
            "course_id": course_id,
            "role": role,
        },
    )
    raise_for_status_with_body(response, "Create enrollment")
    return response.json()


def leave_course(user_id, course_id):
    response = requests.post(
        f"{BASE_URL}/leave_course",
        json={
            "user_id": user_id,
            "course_id": course_id,
        },
    )
    raise_for_status_with_body(response, "Leave course")
    return response.json()


def get_user_enrollments(user_id):
    response = requests.get(
        f"{BASE_URL}/get_user_enrollments",
        params={"user_id": user_id},
    )
    raise_for_status_with_body(response, "Get user enrollments")
    return response.json()


def upload_autograder(assignment_id, zip_path, timeout="10"):
    url = f"{BASE_URL}/upload_assignment_autograder"

    with open(zip_path, "rb") as file:
        files = {"file": (os.path.basename(zip_path), file, "application/zip")}
        data = {
            "assignment_id": assignment_id,
            "autograder_timeout": timeout,
        }
        response = requests.post(url, files=files, data=data)

    raise_for_status_with_body(response, "Upload autograder")
    return response.json()


def delete_assignment(assignment_id):
    if not assignment_id:
        return None

    url = f"{BASE_URL}/delete_assignment?assignment_id={assignment_id}"
    response = requests.delete(url)
    raise_for_status_with_body(response, "Delete assignment")
    return response.json()


def upload_submission(assignment_id, student_id=None, submission_file_path=None):
    url = f"{BASE_URL}/upload_submission"

    if submission_file_path is None:
        submission_file_path = os.path.abspath("dummy_submission.py")
        with open(submission_file_path, "w", encoding="utf-8") as file:
            file.write("print('Hello from stress test')")

    if student_id is None:
        student_id = str(uuid.uuid4())

    with open(submission_file_path, "rb") as file:
        files = {"file": (os.path.basename(submission_file_path), file, "text/x-python")}
        data = {
            "assignment_id": assignment_id,
            "student_id": student_id,
        }
        response = requests.post(url, files=files, data=data)

    raise_for_status_with_body(response, "Upload submission")
    return response.json()


def add_user(name="Stress Student", email=None, password="test123", eid=None, role="Student"):
    url = f"{BASE_URL}/create_user"

    if email is None:
        email = f"{uuid.uuid4().hex[:8]}@example.com"
    if eid is None:
        eid = uuid.uuid4().hex[:8]

    payload = {
        "name": name,
        "email_address": email,
        "password": password,
        "eid": eid,
        "role": role,
    }

    response = requests.post(url, json=payload)

    if response.status_code == 409:
        print("User already exists. Attempting to fetch by email...")
        user_lookup = requests.get(f"{BASE_URL}/get_user_by_email", params={"email": email})
        raise_for_status_with_body(user_lookup, "Get user by email")
        return user_lookup.json()["id"]

    if response.status_code >= 400:
        print("Create user payload:")
        print(payload)

    raise_for_status_with_body(response, "Create user")
    return response.json()["id"]


def delete_user(user_id):
    if not user_id:
        return None

    url = f"{BASE_URL}/delete_user"
    response = requests.delete(url, params={"id": user_id})

    if response.status_code != 200:
        raise Exception(f"Failed to delete user {user_id}: {response.text}")

    try:
        return response.json()
    except ValueError:
        return response.text
