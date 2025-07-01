import requests
import threading
import uuid
import json
import os
import argparse
from utils import create_assignment, upload_autograder, delete_assignment

"""
This is a **stress test script** and will NOT be run with `make test`.

- It does NOT follow pytest conventions (file doesn't start with `test_` or isn't in the default test path).
- It is meant to be run manually to simulate high load.

To run manually:
$ python create_assignments.py num_threads valid_course_id

Make sure to:
- Update the COURSE_ID in the file with a valid one before running.
- Run `flask` or the backend server first.

"""

ASSIGNMENT_IDS_FILE = "generated_assignments.json"
AUTOGRADER_ZIP_PATH = os.path.abspath(os.path.join("..", "..", "assignment-examples", "A1", "A1.zip"))

created_assignments = []

def create_assignment_with_autograder(index, course_id):
    print(f"course id in method: {course_id}")
    try:
        name = f"Stress Assignment {index}"
        assignment_id = create_assignment(name, course_id)
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
    parser = argparse.ArgumentParser(description="Stress test for creating assignments.")
    parser.add_argument(
        "num_threads",
        type=int,
        help="Number of concurrent assignment creations"
    )
    parser.add_argument(
        "course_id",
        type=str,
        help="valid course id under which assignments will be created"
    )
    args = parser.parse_args()
    num_threads = args.num_threads
    print(f"Running stress test with {num_threads} threads...")

    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=create_assignment_with_autograder, args=(i, args.course_id))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    #save created assignment IDs
    with open(ASSIGNMENT_IDS_FILE, "w") as f:
        json.dump(created_assignments, f)
    print(f"\n Assignments saved to {ASSIGNMENT_IDS_FILE}: {created_assignments}")

    #delete created assignments
    for assignment in created_assignments:
        delete_assignment(assignment_id=assignment)

if __name__ == "__main__":
    main()
