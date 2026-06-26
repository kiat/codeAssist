"""
Stress test for concurrent enrollment and leave-course operations.

This version matches the current backend routes:
- POST /create_enrollment with student_id and course_id
- POST /leave_course with user_id and course_id
- GET /get_user_enrollments with user_id
"""

import argparse
import random
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import (
    add_user,
    create_enrollment,
    delete_user,
    get_user_enrollments,
    is_http_status,
    leave_course,
)


test_results = []
results_lock = threading.Lock()
created_users = []
users_lock = threading.Lock()


def is_user_enrolled(user_id: str, course_id: str) -> bool:
    courses = get_user_enrollments(user_id)
    return any(course.get("id") == course_id for course in courses)


def run_enrollment_operations(
    user_id: str,
    course_id: str,
    thread_id: int,
    operations_count: int,
    randomize: bool,
) -> dict:
    thread_results = {
        "thread_id": thread_id,
        "user_id": user_id,
        "total_operations": operations_count,
        "successful_operations": 0,
        "handled_conflicts": 0,
        "failed_operations": 0,
        "operations": [],
        "errors": [],
    }

    print(f"[thread {thread_id}] starting {operations_count} enrollment operations")

    for operation_num in range(operations_count):
        if randomize:
            operation = "enroll" if operation_num == 0 or random.choice([True, False]) else "leave"
        else:
            operation = "enroll" if operation_num % 2 == 0 else "leave"

        start_time = time.time()
        try:
            if operation == "enroll":
                create_enrollment(user_id, course_id)
                expected_enrolled = True
            else:
                leave_course(user_id, course_id)
                expected_enrolled = False

            duration = time.time() - start_time
            actual_enrolled = is_user_enrolled(user_id, course_id)
            consistent = actual_enrolled == expected_enrolled

            thread_results["successful_operations"] += 1
            thread_results["operations"].append(
                {
                    "operation_num": operation_num,
                    "operation": operation,
                    "duration": duration,
                    "success": True,
                    "consistent": consistent,
                    "expected_enrolled": expected_enrolled,
                    "actual_enrolled": actual_enrolled,
                }
            )

            consistency = "consistent" if consistent else "state changed by race"
            print(
                f"[thread {thread_id}] op {operation_num}: "
                f"PASS {operation} in {duration:.3f}s ({consistency})"
            )

        except Exception as error:
            duration = time.time() - start_time
            expected_conflict = is_http_status(error, 404, 409)

            if expected_conflict:
                thread_results["handled_conflicts"] += 1
                status = "CONFLICT"
            else:
                thread_results["failed_operations"] += 1
                thread_results["errors"].append(str(error))
                status = "FAIL"

            thread_results["operations"].append(
                {
                    "operation_num": operation_num,
                    "operation": operation,
                    "duration": duration,
                    "success": False,
                    "handled_conflict": expected_conflict,
                    "error": str(error),
                }
            )

            print(f"[thread {thread_id}] op {operation_num}: {status} {operation}: {error}")

        time.sleep(random.uniform(0.01, 0.05))

    with results_lock:
        test_results.append(thread_results)

    completed = thread_results["successful_operations"] + thread_results["handled_conflicts"]
    print(f"[thread {thread_id}] completed {completed}/{operations_count} handled")
    return thread_results


def create_test_users(num_users: int) -> list[str]:
    print(f"Creating {num_users} test users")

    user_ids = []
    for index in range(num_users):
        try:
            user_name = f"enrollment_test_user_{index}_{uuid.uuid4().hex[:8]}"
            user_id = add_user(name=user_name)
            user_ids.append(user_id)

            with users_lock:
                created_users.append(user_id)

            print(f"- user {index + 1}/{num_users}: {user_id}")

        except Exception as error:
            print(f"- failed to create user {index + 1}: {error}")

    return user_ids


def print_results_summary() -> None:
    print()
    print("=" * 80)
    print("CONCURRENT ENROLLMENT STRESS TEST RESULTS")
    print("=" * 80)

    total_threads = len(test_results)
    total_operations = sum(result["total_operations"] for result in test_results)
    total_successful = sum(result["successful_operations"] for result in test_results)
    total_conflicts = sum(result["handled_conflicts"] for result in test_results)
    total_failed = sum(result["failed_operations"] for result in test_results)
    handled = total_successful + total_conflicts
    handled_rate = (handled / total_operations * 100) if total_operations else 0

    print(f"Total threads: {total_threads}")
    print(f"Total operations: {total_operations}")
    print(f"Successful operations: {total_successful}")
    print(f"Handled conflicts/races: {total_conflicts}")
    print(f"Unexpected failures: {total_failed}")
    print(f"Handled rate: {handled_rate:.1f}%")
    print()

    operation_times = [
        operation["duration"]
        for result in test_results
        for operation in result["operations"]
        if "duration" in operation
    ]
    if operation_times:
        print("Performance:")
        print(f"- Average operation time: {sum(operation_times) / len(operation_times):.3f}s")
        print(f"- Fastest operation: {min(operation_times):.3f}s")
        print(f"- Slowest operation: {max(operation_times):.3f}s")
        print()

    print(f"{'Thread':<8} {'Success':>8} {'Conflict':>10} {'Failed':>8}")
    print("-" * 40)
    for result in sorted(test_results, key=lambda item: item["thread_id"]):
        print(
            f"{result['thread_id']:<8} "
            f"{result['successful_operations']:>8} "
            f"{result['handled_conflicts']:>10} "
            f"{result['failed_operations']:>8}"
        )

    failures = [
        error
        for result in test_results
        for error in result["errors"]
    ]
    if failures:
        print()
        print("Failure details:")
        for error in failures[:10]:
            print(f"- {error}")

    print("=" * 80)


def cleanup() -> None:
    print()
    print("Cleanup:")

    deleted_count = 0
    for user_id in created_users:
        try:
            delete_user(user_id)
            deleted_count += 1
        except Exception as error:
            print(f"- Failed to delete user {user_id}: {error}")

    print(f"- Deleted users: {deleted_count}/{len(created_users)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Concurrent enrollment stress test.")
    parser.add_argument("course_id", type=str, help="Valid course ID")
    parser.add_argument("--num_threads", type=int, default=5, help="Number of threads")
    parser.add_argument(
        "--operations_per_thread",
        type=int,
        default=10,
        help="Number of enroll/leave operations per thread",
    )
    parser.add_argument(
        "--users_per_thread",
        type=int,
        default=1,
        help="Number of users per thread",
    )
    parser.add_argument(
        "--max_workers",
        type=int,
        default=10,
        help="Maximum concurrent workers",
    )
    parser.add_argument(
        "--randomize",
        action="store_true",
        help="Randomize enroll/leave choices instead of alternating them",
    )
    parser.add_argument("--cleanup", action="store_true", help="Delete created users")

    args = parser.parse_args()

    if args.num_threads < 1 or args.operations_per_thread < 1 or args.users_per_thread < 1:
        print("Failed to run stress test: thread, operation, and user counts must be >= 1")
        return 1

    total_users_needed = args.num_threads * args.users_per_thread

    print("Starting concurrent enrollment stress test")
    print(f"Course ID: {args.course_id}")
    print(f"Threads: {args.num_threads}")
    print(f"Operations per thread: {args.operations_per_thread}")
    print(f"Users per thread: {args.users_per_thread}")
    print(f"Max workers: {args.max_workers}")

    try:
        user_ids = create_test_users(total_users_needed)
        if not user_ids:
            print("Failed to run stress test: no users were created")
            return 1

        tasks = []
        user_index = 0
        for thread_id in range(args.num_threads):
            if user_index >= len(user_ids):
                break
            primary_user = user_ids[user_index]
            user_index += args.users_per_thread
            tasks.append((primary_user, args.course_id, thread_id, args.operations_per_thread))

        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = [
                executor.submit(
                    run_enrollment_operations,
                    user_id,
                    course_id,
                    thread_id,
                    operations_count,
                    args.randomize,
                )
                for user_id, course_id, thread_id, operations_count in tasks
            ]

            for future in as_completed(futures):
                future.result()

        print_results_summary()

        if args.cleanup:
            cleanup()

        unexpected_failures = sum(
            result["failed_operations"] for result in test_results
        )
        if unexpected_failures:
            print("Failed to run stress test: unexpected enrollment failures occurred")
            return 1

        return 0

    except Exception as error:
        print(f"Failed to run stress test: {error}")
        if args.cleanup:
            cleanup()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
