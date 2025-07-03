import argparse
import os
import threading
from utils import create_assignment, upload_autograder, upload_submission, add_user, delete_user, delete_assignment

"""
Stress test script for multi-student submissions.

Usage:
    python stress_upload.py <course_id> [--num_threads N] [--cleanup]

Example:
    python stress_upload.py 123e4567-e89b-12d3-a456-426614174000 --num_threads 10 --cleanup

- Creates an assignment and uploads an autograder.
- Spawns N threads to create students and upload submissions.
- If --cleanup is set, deletes the assignment (students not deleted by default).
"""

AUTOGRADER_ZIP_PATH = os.path.abspath(os.path.join("..", "..", "assignment-examples", "A1", "A1.zip"))
SUBMISSION_PATH = os.path.join("..", "..", "assignment-examples", "A1", "calculator.py")

# Shared state
created_students = []
created_students_lock = threading.Lock()
assignment_id = None


def upload_for_student(assignment_id: str, index: int):
    try:
        student_name = f"new student{index}"
        student_id = add_user(name=student_name)
        with created_students_lock:
            created_students.append(student_id)
       
        print(f"[Thread-{index}] Added student: {student_name} ({student_id})")

        if not os.path.isfile(SUBMISSION_PATH):
            print(f"[Thread-{index}] Submission file not found at: {SUBMISSION_PATH}")
            return

        upload_submission(assignment_id=assignment_id, student_id=student_id, submission_file_path=SUBMISSION_PATH)
        print(f"[Thread-{index}] ✅ Submission uploaded for {student_name}")

       

    except Exception as e:
        print(f"[Thread-{index}] Error uploading submission: {e}")


def cleanup():
    print(" Starting cleanup of created students and assignment...")
    # for student_id in created_students:
    #     try:
    #         delete_user(student_id)
    #         print(f"Deleted student: {student_id}")
    #     except Exception as e:
    #         print(f"Failed to delete student {student_id}: {e}")
    try:
        delete_assignment(assignment_id)
        print(f" Deleted assignment: {assignment_id}")
    except Exception as e:
        print(f" Failed to delete assignment: {e}")
    print(" Cleanup complete.")


def main():
    global assignment_id
    parser = argparse.ArgumentParser(description="Multi-student submission uploader.")
    parser.add_argument("course_id", type=str, help="Valid course ID")
    parser.add_argument("--num_threads", type=int, default=5, help="Number of concurrent submissions")
    parser.add_argument("--cleanup", action="store_true", help="Delete the created assignment and students")
    args = parser.parse_args()

    print(f" Creating shared assignment in course {args.course_id}...")
    try:
        assignment_id = create_assignment("Multithreaded Test Assignment", args.course_id)
        print(f" Assignment created with ID: {assignment_id}")

        upload_autograder(assignment_id, AUTOGRADER_ZIP_PATH)
        print(" Autograder uploaded")

        threads = []
        for i in range(args.num_threads):
            t = threading.Thread(target=upload_for_student, args=(assignment_id, i))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        print(" All submissions uploaded. Cleaning new data from db...")
        if args.cleanup:
            cleanup()
            return

    except Exception as e:
        print(f" Failed to run stress test: {e}")

if __name__ == "__main__":
    main()
