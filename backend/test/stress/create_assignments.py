import argparse
import json
import os
import threading
import uuid

from utils import create_assignment, upload_autograder, delete_assignment

"""
This is a stress test script and will NOT be run with `make test`.

- It does NOT follow pytest conventions.
- It is meant to be run manually to simulate high load.

To run manually:
$ python create_assignments.py num_threads valid_course_id

Make sure to:
- Use a valid course ID.
- Run the backend server first.
"""

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

ASSIGNMENT_IDS_FILE = os.path.join(
    SCRIPT_DIR,
    "results",
    "generated_assignments.json",
)

AUTOGRADER_ZIP_PATH = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "..", "assignment-examples", "A1", "A1.zip")
)

created_assignments = []
created_assignments_lock = threading.Lock()
assignment_errors = []
assignment_errors_lock = threading.Lock()


def record_error(message):
    with assignment_errors_lock:
        assignment_errors.append(message)


def create_assignment_with_autograder(index, course_id):
    try:
        name = f"Stress Assignment {index}_{uuid.uuid4().hex[:8]}"
        print(f"[Assignment {index}] Creating assignment: {name}")

        assignment_id = create_assignment(name, course_id)

        if not assignment_id:
            message = f"[Assignment {index}] Failed to create assignment"
            print(message)
            record_error(message)
            return

        print(f"[Assignment {index}] Created -> {assignment_id}")

        with created_assignments_lock:
            created_assignments.append(assignment_id)

        if not os.path.exists(AUTOGRADER_ZIP_PATH):
            message = f"[Assignment {index}] Autograder zip not found at {AUTOGRADER_ZIP_PATH}"
            print(message)
            record_error(message)
            return

        result = upload_autograder(assignment_id, AUTOGRADER_ZIP_PATH)
        print(f"[Assignment {index}] Autograder uploaded -> {result}")

    except Exception as error:
        message = f"[Assignment {index}] Error: {error}"
        print(message)
        record_error(message)


def main():
    parser = argparse.ArgumentParser(description="Stress test for creating assignments.")
    parser.add_argument(
        "num_threads",
        type=int,
        help="Number of concurrent assignment creations",
    )
    parser.add_argument(
        "course_id",
        type=str,
        help="Valid course ID under which assignments will be created",
    )
    parser.set_defaults(cleanup=True)
    parser.add_argument(
        "--cleanup",
        dest="cleanup",
        action="store_true",
        help="Delete created assignments after the test. Default: enabled.",
    )
    parser.add_argument(
        "--no-cleanup",
        dest="cleanup",
        action="store_false",
        help="Keep created assignments for manual inspection.",
    )
    args = parser.parse_args()

    if args.num_threads < 1:
        print("Failed to run stress test: num_threads must be at least 1")
        return 1

    print(f"Running stress test with {args.num_threads} threads...")
    print(f"Course ID: {args.course_id}")
    print(f"Cleanup enabled: {args.cleanup}")

    threads = []

    for index in range(args.num_threads):
        thread = threading.Thread(
            target=create_assignment_with_autograder,
            args=(index, args.course_id),
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    os.makedirs(os.path.dirname(ASSIGNMENT_IDS_FILE), exist_ok=True)

    with open(ASSIGNMENT_IDS_FILE, "w", encoding="utf-8") as file:
        json.dump(created_assignments, file, indent=2)

    print()
    print(f"Assignments saved to {ASSIGNMENT_IDS_FILE}: {created_assignments}")

    if assignment_errors:
        print()
        print("Assignment creation errors:")
        for error in assignment_errors:
            print(f"- {error}")

    if args.cleanup:
        deleted_count = 0

        for assignment_id in created_assignments:
            if assignment_id:
                try:
                    delete_assignment(assignment_id=assignment_id)
                    deleted_count += 1
                except Exception as error:
                    print(f"Failed to delete assignment {assignment_id}: {error}")

        print(f"Cleanup complete. Deleted {deleted_count}/{len(created_assignments)} assignments.")
    else:
        print("Cleanup skipped. Created assignments were left in the course.")

    if assignment_errors:
        print("Failed to run stress test: one or more assignment workers failed")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
