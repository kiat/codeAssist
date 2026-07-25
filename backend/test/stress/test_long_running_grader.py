"""
Stress test for long-running grading operations.

The backend grades submissions synchronously inside /upload_submission, so this
script measures the HTTP request duration directly instead of sleeping after
submission. It uses the A1 calculator fixture with a controlled sleep prepended
so the submitted file still matches the autograder's expected shape.
"""

import argparse
import os
import shutil
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import (
    add_user,
    create_assignment,
    delete_assignment,
    delete_user,
    upload_autograder,
    upload_submission,
)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AUTOGRADER_ZIP_PATH = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "..", "assignment-examples", "A1", "A1.zip")
)
SUBMISSION_TEMPLATE_PATH = os.path.abspath(
    os.path.join(SCRIPT_DIR, "..", "..", "assignment-examples", "A1", "calculator.py")
)

TEST_CASES = [
    {"name": "quick_execution", "execution_time": 1},
    {"name": "medium_execution", "execution_time": 5},
    {"name": "long_execution", "execution_time": 10},
    {"name": "very_long_execution", "execution_time": 20},
]

created_students = []
created_students_lock = threading.Lock()
test_results = []
results_lock = threading.Lock()
assignment_id = None


def create_delayed_submission_file(execution_time: int, filename_prefix: str) -> tuple[str, str]:
    temp_dir = tempfile.mkdtemp(prefix=f"{filename_prefix}_")
    submission_path = os.path.join(temp_dir, "calculator.py")

    with open(SUBMISSION_TEMPLATE_PATH, "r", encoding="utf-8") as source:
        template = source.read()

    with open(submission_path, "w", encoding="utf-8") as target:
        target.write("import time\n")
        target.write(f"time.sleep({execution_time})\n\n")
        target.write(template)

    return temp_dir, submission_path


def submit_and_measure(test_config: dict, thread_index: int, current_assignment_id: str) -> dict:
    student_id = None
    temp_dir = None
    start_time = time.time()

    try:
        student_name = (
            f"long_runner_{test_config['name']}_{thread_index}_{uuid.uuid4().hex[:8]}"
        )
        student_id = add_user(name=student_name)

        with created_students_lock:
            created_students.append(student_id)

        temp_dir, submission_file = create_delayed_submission_file(
            test_config["execution_time"],
            test_config["name"],
        )

        print(
            f"[worker {thread_index}] submitting {test_config['name']} "
            f"(delay {test_config['execution_time']}s)"
        )

        upload_submission(
            assignment_id=current_assignment_id,
            student_id=student_id,
            submission_file_path=submission_file,
        )

        duration = time.time() - start_time
        result = {
            "test_name": test_config["name"],
            "thread_index": thread_index,
            "student_id": student_id,
            "expected_execution_time": test_config["execution_time"],
            "duration": duration,
            "success": True,
            "error": None,
        }
        print(f"[worker {thread_index}] PASS {test_config['name']} in {duration:.2f}s")
        return result

    except Exception as error:
        duration = time.time() - start_time
        result = {
            "test_name": test_config["name"],
            "thread_index": thread_index,
            "student_id": student_id,
            "expected_execution_time": test_config["execution_time"],
            "duration": duration,
            "success": False,
            "error": str(error),
        }
        print(f"[worker {thread_index}] FAIL {test_config['name']}: {error}")
        return result

    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)


def print_results_summary() -> None:
    print()
    print("=" * 80)
    print("LONG-RUNNING GRADER STRESS TEST RESULTS")
    print("=" * 80)

    total = len(test_results)
    successful = [result for result in test_results if result["success"]]
    failed = [result for result in test_results if not result["success"]]
    success_rate = (len(successful) / total * 100) if total else 0

    print(f"Total submissions: {total}")
    print(f"Successful submissions: {len(successful)} ({success_rate:.1f}%)")
    print(f"Failed submissions: {len(failed)}")
    print()
    print(f"{'Status':<8} {'Case':<24} {'Expected':>10} {'Actual':>10}")
    print("-" * 58)

    for result in test_results:
        status = "PASS" if result["success"] else "FAIL"
        expected = f"{result['expected_execution_time']}s"
        actual = f"{result['duration']:.2f}s"
        print(f"{status:<8} {result['test_name']:<24} {expected:>10} {actual:>10}")

    if failed:
        print()
        print("Failure details:")
        for result in failed:
            print(f"- {result['test_name']}: {result['error']}")

    print("=" * 80)


def cleanup(current_assignment_id: str | None) -> None:
    print()
    print("Cleanup:")

    if current_assignment_id:
        try:
            delete_assignment(current_assignment_id)
            print(f"- Deleted assignment: {current_assignment_id}")
        except Exception as error:
            print(f"- Failed to delete assignment {current_assignment_id}: {error}")

    deleted_students = 0
    for student_id in created_students:
        try:
            delete_user(student_id)
            deleted_students += 1
        except Exception as error:
            print(f"- Failed to delete student {student_id}: {error}")

    print(f"- Deleted students: {deleted_students}/{len(created_students)}")


def main() -> int:
    global assignment_id

    parser = argparse.ArgumentParser(description="Long-running grader stress test.")
    parser.add_argument("course_id", type=str, help="Valid course ID")
    parser.add_argument(
        "--max_execution_time",
        type=int,
        default=20,
        help="Maximum controlled delay to test, in seconds",
    )
    parser.add_argument(
        "--num_submissions",
        type=int,
        default=1,
        help="Number of submissions per selected delay",
    )
    parser.add_argument(
        "--max_workers",
        type=int,
        default=2,
        help="Maximum number of concurrent submission workers",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete created assignment and users after the test",
    )

    args = parser.parse_args()

    if args.num_submissions < 1:
        print("Failed to run stress test: --num_submissions must be at least 1")
        return 1

    if args.max_workers < 1:
        print("Failed to run stress test: --max_workers must be at least 1")
        return 1

    if not os.path.isfile(AUTOGRADER_ZIP_PATH):
        print(f"Failed to run stress test: autograder zip not found at {AUTOGRADER_ZIP_PATH}")
        return 1

    if not os.path.isfile(SUBMISSION_TEMPLATE_PATH):
        print(f"Failed to run stress test: submission template not found at {SUBMISSION_TEMPLATE_PATH}")
        return 1

    selected_tests = [
        test for test in TEST_CASES if test["execution_time"] <= args.max_execution_time
    ]
    if not selected_tests:
        print(f"Failed to run stress test: no cases <= {args.max_execution_time}s")
        return 1

    print("Starting long-running grader stress test")
    print(f"Course ID: {args.course_id}")
    print(f"Selected delays: {[test['execution_time'] for test in selected_tests]}")
    print(f"Submissions per delay: {args.num_submissions}")
    print(f"Max workers: {args.max_workers}")

    try:
        assignment_name = f"Long Running Grader {uuid.uuid4().hex[:8]}"
        assignment_id = create_assignment(
            assignment_name,
            args.course_id,
            published=True,
            published_date=None,
            due_date=None,
        )
        print(f"Created published assignment: {assignment_id}")

        upload_autograder(assignment_id, AUTOGRADER_ZIP_PATH)
        print("Uploaded autograder")

        tasks = []
        for test_config in selected_tests:
            for copy_index in range(args.num_submissions):
                tasks.append((test_config, copy_index))

        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = [
                executor.submit(submit_and_measure, test_config, index, assignment_id)
                for index, (test_config, _) in enumerate(tasks)
            ]
            for future in as_completed(futures):
                with results_lock:
                    test_results.append(future.result())

        print_results_summary()

        if args.cleanup:
            cleanup(assignment_id)

        failures = [result for result in test_results if not result["success"]]
        if failures:
            print("Failed to run stress test: one or more long-running submissions failed")
            return 1

        return 0

    except Exception as error:
        print(f"Failed to run stress test: {error}")
        if args.cleanup:
            cleanup(assignment_id)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
