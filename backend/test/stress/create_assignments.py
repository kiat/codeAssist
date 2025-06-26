import requests
import threading
import uuid
import json
import os
from utils import create_assignment, upload_autograder, delete_assignment, create_course, delete_course

"""
This is a **stress test script** and will NOT be run with `make test`.

- It does NOT follow pytest conventions (file doesn't start with `test_` or isn't in the default test path).
- It is meant to be run manually to simulate high load.

To run manually:
$ python stress_create_assignments.py

Make sure to:
- Update the COURSE_ID in the file with a valid one before running.
- Run `flask` or the backend server first.

"""


COURSE_ID = "13f225b9-46eb-498a-85b3-ff068836986c"  # Replace with working course id!
ASSIGNMENT_IDS_FILE = "generated_assignments.json"
AUTOGRADER_ZIP_PATH = os.path.abspath(os.path.join("..", "..", "assignment-examples", "A1", "A1.zip"))

created_assignments = []

def create_assignment_with_autograder(index):
    try:
        name = f"Stress Assignment {index}"
        assignment_id = create_assignment(name, COURSE_ID)
        print(f"[Assignment {index}] Created → {assignment_id}")
        created_assignments.append(assignment_id)

        if not os.path.exists(AUTOGRADER_ZIP_PATH):
            print(f"[Assignment {index}] Autograder zip not found at {AUTOGRADER_ZIP_PATH}")
            return

        result = upload_autograder(assignment_id, AUTOGRADER_ZIP_PATH)
        print(f"[Assignment {index}] Autograder uploaded → {result}")

    except Exception as e:
        print(f"[Assignment {index}] Error: {e}")

def main():
    threads = []
    for i in range(100): #increase load here
        t = threading.Thread(target=create_assignment_with_autograder, args=(i,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    #save created assignment IDs
    with open(ASSIGNMENT_IDS_FILE, "w") as f:
        json.dump(created_assignments, f)
    print(f"\n Passed! Assignments saved to {ASSIGNMENT_IDS_FILE}: {created_assignments}")

    #delete created assignments
    for assignment in created_assignments:
        delete_assignment(assignment_id=assignment)

if __name__ == "__main__":
    main()
