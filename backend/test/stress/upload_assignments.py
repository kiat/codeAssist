import argparse
import os
import threading
from utils import create_assignment, upload_autograder, upload_submission, add_user

AUTOGRADER_ZIP_PATH = os.path.abspath(os.path.join("..", "..", "assignment-examples", "A1", "A1.zip"))
SUBMISSION_PATH = os.path.join("..", "..", "assignment-examples", "A1", "calculator.py")


def upload_for_student(assignment_id: str, index: int):
    try:
        student_name = f"stress-student{index}"
        student_id = add_user(name=student_name)
        print(f"[Thread-{index}] Added student: {student_name} ({student_id})")

        if not os.path.isfile(SUBMISSION_PATH):
            print(f"[Thread-{index}] Submission file not found at: {SUBMISSION_PATH}")
            return

        upload_submission(assignment_id=assignment_id, student_id=student_id, submission_file_path=SUBMISSION_PATH)
        print(f"[Thread-{index}]  Submission uploaded for {student_name}")

    except Exception as e:
        print(f"[Thread-{index}]  Error uploading submission: {e}")

def main():
    parser = argparse.ArgumentParser(description="Multi-student submission uploader.")
    parser.add_argument("num_threads", type=int, help="Number of concurrent submissions")
    parser.add_argument("course_id", type=str, help="Valid course ID")
    args = parser.parse_args()

    print(f"Creating shared assignment in course {args.course_id}...")
    try:
        assignment_id = create_assignment("Multithreaded Test Assignment", args.course_id)
        print(f"Assignment created with ID: {assignment_id}")

        upload_autograder(assignment_id, AUTOGRADER_ZIP_PATH)
        print("Autograder uploaded")

        threads = []
        for i in range(args.num_threads):
            t = threading.Thread(target=upload_for_student, args=(assignment_id, i))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

    except Exception as e:
        print(f"Failed to set up shared assignment: {e}")

if __name__ == "__main__":
    main()
