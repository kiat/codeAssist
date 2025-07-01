import requests
import os
import uuid


BASE_URL = "http://localhost:5001"

def create_assignment(name, course_id):
    url = f"{BASE_URL}/create_assignment"
    payload = {
        "name": name,
        "course_id": course_id
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["id"]

def upload_autograder(assignment_id, zip_path, timeout="10"):
    url = f"{BASE_URL}/upload_assignment_autograder"
    with open(zip_path, "rb") as f:
        files = {"file": (os.path.basename(zip_path), f, "application/zip")}
        data = {
            "assignment_id": assignment_id,
            "autograder_timeout": timeout
        }
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()
        return response.json()

def delete_assignment(assignment_id):
    url = f"{BASE_URL}/delete_assignment?assignment_id={assignment_id}"
    response = requests.delete(url)
    response.raise_for_status()
    return response.json()

def upload_submission(assignment_id, student_id=None, submission_file_path=None):
    url = f"{BASE_URL}/upload_submission"

    # Use a default dummy Python file if none provided
    if submission_file_path is None:
        submission_file_path = os.path.abspath("dummy_submission.py")
        with open(submission_file_path, "w") as f:
            f.write("print('Hello from stress test')")

    if student_id is None:
        student_id = str(uuid.uuid4())

    with open(submission_file_path, "rb") as file:
        files = {"file": (os.path.basename(submission_file_path), file, "text/x-python")}
        data = {
            "assignment_id": assignment_id,
            "student_id": student_id
        }
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()
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
        "role": role
    }

    response = requests.post(url, json=payload)
    
    # If user already exists (email or EID), fetch their ID instead
    if response.status_code == 409:
        print("User already exists. Attempting to fetch by email...")
        user_lookup = requests.get(f"{BASE_URL}/get_user_by_email", params={"email": email})
        user_lookup.raise_for_status()
        return user_lookup.json()["id"]
    
    response.raise_for_status()
    return response.json()["id"]

