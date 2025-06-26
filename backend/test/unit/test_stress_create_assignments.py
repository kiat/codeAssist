import requests
import threading
import uuid
import json
import os
from utils import create_assignment, upload_autograder

COURSE_ID = "a3eb254c-9030-4648-a0b3-b16ec2749787"  # Replace if needed
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
    for i in range(2):  # Create 2 assignments
        t = threading.Thread(target=create_assignment_with_autograder, args=(i,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # Save created assignment IDs
    with open(ASSIGNMENT_IDS_FILE, "w") as f:
        json.dump(created_assignments, f)
    print(f"\n Finished. Assignments saved to {ASSIGNMENT_IDS_FILE}: {created_assignments}")

if __name__ == "__main__":
    main()
