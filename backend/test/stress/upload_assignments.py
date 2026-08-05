import argparse
import os
import threading
import uuid

from utils import (
    add_user,
    create_assignment,
    delete_assignment,
    delete_user,
    upload_autograder,
    upload_submission,
)

"""
Stress test script for multi-student submissions.

Usage:
    python upload_assignments.py <course_id> [--num_threads N] [--cleanup]

Example:
    python upload_assignments.py 123e4567-e89b-12d3-a456-426614174000 --num_threads 10 --cleanup

- Creates one published assignment and uploads an autograder.
- Spawns N threads to create students and upload submissions.
- If --cleanup is set, deletes the created assignment and created students.
"""

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

AUTOGRADER_ZIP_PATH = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "..", "assignment-examples", "A1", "A1.zip")
)

SUBMISSION_PATH = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "..", "assignment-examples", "A1", "calculator.py")
)

created_students = []
created_students_lock = threading.Lock()

submission_errors = []
submission_errors_lock = threading.Lock()

assignment_id = None


def record_error(message: str) -> None:
    with submission_errors_lock:
        submission_errors.append(message)


def upload_for_student(current_assignment_id: str, index: int) -> None:
    try:
        unique_suffix = uuid.uuid4().hex[:8]
        student_name = f"stress_student_{index}_{unique_suffix}"

        student_id = add_user(name=student_name)

        with created_students_lock:
            created_students.append(student_id)

        print(f"[Thread-{index}] Added student: {student_name} ({student_id})")

        if not os.path.isfile(SUBMISSION_PATH):
            message = f"[Thread-{index}] Submission file not found at: {SUBMISSION_PATH}"
            print(message)
            record_error(message)
            return

        upload_submission(
            assignment_id=current_assignment_id,
            student_id=student_id,
            submission_file_path=SUBMISSION_PATH,
        )

        print(f"[Thread-{index}] Submission uploaded for {student_name}")

    except Exception as error:
        message = f"[Thread-{index}] Error uploading submission: {error}"
        print(message)
        record_error(message)


def cleanup_created_data(current_assignment_id: str | None) -> None:
    print("Starting cleanup of created students and assignment...")

    if current_assignment_id:
        try:
            delete_assignment(current_assignment_id)
            print(f"Deleted assignment: {current_assignment_id}")
        except Exception as error:
            print(f"Failed to delete assignment {current_assignment_id}: {error}")

    deleted_students = 0

    for student_id in created_students:
        try:
            delete_user(student_id)
            deleted_students += 1
            print(f"Deleted student: {student_id}")
        except Exception as error:
            print(f"Failed to delete student {student_id}: {error}")

    print(
        f"Cleanup complete. Deleted {deleted_students}/{len(created_students)} students."
    )


def main() -> int:
    global assignment_id

    parser = argparse.ArgumentParser(description="Multi-student submission uploader.")
    parser.add_argument("course_id", type=str, help="Valid course ID")
    parser.add_argument(
        "--num_threads",
        type=int,
        default=5,
        help="Number of concurrent submissions",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete the created assignment and students",
    )

    args = parser.parse_args()

    if args.num_threads < 1:
        print("Failed to run stress test: --num_threads must be at least 1")
        return 1

    if not os.path.isfile(AUTOGRADER_ZIP_PATH):
        print(f"Failed to run stress test: autograder zip not found at {AUTOGRADER_ZIP_PATH}")
        return 1

    if not os.path.isfile(SUBMISSION_PATH):
        print(f"Failed to run stress test: submission file not found at {SUBMISSION_PATH}")
        return 1

    assignment_name = f"Multithreaded Test Assignment {uuid.uuid4().hex[:8]}"

    print(f"Creating shared assignment in course {args.course_id}...")
    print(f"Assignment name: {assignment_name}")

    try:
        assignment_id = create_assignment(
            assignment_name,
            args.course_id,
            published=True,
            published_date=None,
            due_date=None,
        )

        print(f"Assignment created with ID: {assignment_id}")

        upload_autograder(assignment_id, AUTOGRADER_ZIP_PATH)
        print("Autograder uploaded")

        threads = []

        for index in range(args.num_threads):
            thread = threading.Thread(
                target=upload_for_student,
                args=(assignment_id, index),
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        successful_submissions = args.num_threads - len(submission_errors)

        print()
        print("Submission stress test summary:")
        print(f"Total requested submissions: {args.num_threads}")
        print(f"Successful submissions: {successful_submissions}")
        print(f"Failed submissions: {len(submission_errors)}")

        if submission_errors:
            print()
            print("Submission errors:")
            for error in submission_errors:
                print(f"- {error}")

        if args.cleanup:
            cleanup_created_data(assignment_id)

        if submission_errors:
            print("Failed to run stress test: one or more submissions failed")
            return 1

        print("All submissions uploaded successfully.")
        return 0

    except Exception as error:
        print(f"Failed to run stress test: {error}")

        if args.cleanup:
            cleanup_created_data(assignment_id)

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
