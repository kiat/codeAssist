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