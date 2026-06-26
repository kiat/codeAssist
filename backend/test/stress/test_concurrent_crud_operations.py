"""
Stress test for concurrent CRUD operations on courses and assignments.

This script matches the current backend routes and separates expected
concurrency conflicts from unexpected backend failures.
"""

import argparse
import random
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils import (
    add_user,
    create_assignment,
    create_course,
    delete_assignment,
    delete_course,
    delete_user,
    get_assignment,
    get_course,
    get_course_assignments,
    is_http_status,
)


test_results = []
results_lock = threading.Lock()
created_courses = []
created_assignments = []
created_users = []
created_lock = threading.Lock()
active_resources = {
    "courses": set(),
    "assignments": set(),
}
resources_lock = threading.Lock()


def add_active(resource_type: str, resource_id: str) -> None:
    with resources_lock:
        active_resources[resource_type].add(resource_id)


def remove_active(resource_type: str, resource_id: str) -> None:
    with resources_lock:
        active_resources[resource_type].discard(resource_id)


def get_active(resource_type: str) -> list[str]:
    with resources_lock:
        return list(active_resources[resource_type])


def remember_created(resource_type: str, resource_id: str) -> None:
    with created_lock:
        if resource_type == "courses":
            created_courses.append(resource_id)
        elif resource_type == "assignments":
            created_assignments.append(resource_id)
        elif resource_type == "users":
            created_users.append(resource_id)


def is_expected_race(error: Exception) -> bool:
    return is_http_status(error, 404, 409)


class ConcurrentCRUDTester:
    def __init__(self, thread_id: int, instructor_id: str):
        self.thread_id = thread_id
        self.instructor_id = instructor_id
        self.operations = []
        self.successful_operations = 0
        self.handled_conflicts = 0
        self.skipped_operations = 0
        self.failed_operations = 0
        self.errors = []

    def log_operation(
        self,
        operation_type: str,
        status: str,
        duration: float,
        details: dict | None = None,
        error: str | None = None,
    ) -> None:
        operation = {
            "type": operation_type,
            "status": status,
            "duration": duration,
            "details": details or {},
            "error": error,
            "timestamp": time.time(),
        }
        self.operations.append(operation)

        if status == "success":
            self.successful_operations += 1
            print(f"[thread {self.thread_id}] PASS {operation_type}: {details}")
        elif status == "conflict":
            self.handled_conflicts += 1
            print(f"[thread {self.thread_id}] CONFLICT {operation_type}: {error}")
        elif status == "skipped":
            self.skipped_operations += 1
            print(f"[thread {self.thread_id}] SKIP {operation_type}: {details}")
        else:
            self.failed_operations += 1
            self.errors.append(error or "unknown error")
            print(f"[thread {self.thread_id}] FAIL {operation_type}: {error}")

    def create_course_operation(self) -> str | None:
        start_time = time.time()
        try:
            course_name = f"Stress Course T{self.thread_id} {uuid.uuid4().hex[:8]}"
            course_id = create_course(course_name, instructor_id=self.instructor_id)
            remember_created("courses", course_id)
            add_active("courses", course_id)
            self.log_operation(
                "CREATE_COURSE",
                "success",
                time.time() - start_time,
                {"course_id": course_id, "name": course_name},
            )
            return course_id
        except Exception as error:
            self.log_operation(
                "CREATE_COURSE",
                "failure",
                time.time() - start_time,
                error=str(error),
            )
            return None

    def delete_course_operation(self, course_id: str) -> bool:
        start_time = time.time()
        try:
            delete_course(course_id)
            remove_active("courses", course_id)
            self.log_operation(
                "DELETE_COURSE",
                "success",
                time.time() - start_time,
                {"course_id": course_id},
            )
            return True
        except Exception as error:
            status = "conflict" if is_expected_race(error) else "failure"
            self.log_operation(
                "DELETE_COURSE",
                status,
                time.time() - start_time,
                {"course_id": course_id},
                str(error),
            )
            return False

    def query_course_operation(self, course_id: str) -> None:
        start_time = time.time()
        try:
            course_data = get_course(course_id)
            self.log_operation(
                "QUERY_COURSE",
                "success",
                time.time() - start_time,
                {"course_id": course_id, "name": course_data.get("name") if course_data else None},
            )
        except Exception as error:
            status = "conflict" if is_expected_race(error) else "failure"
            self.log_operation(
                "QUERY_COURSE",
                status,
                time.time() - start_time,
                {"course_id": course_id},
                str(error),
            )

    def query_course_assignments_operation(self, course_id: str) -> None:
        start_time = time.time()
        try:
            assignments = get_course_assignments(course_id)
            self.log_operation(
                "QUERY_COURSE_ASSIGNMENTS",
                "success",
                time.time() - start_time,
                {"course_id": course_id, "assignment_count": len(assignments)},
            )
        except Exception as error:
            status = "conflict" if is_expected_race(error) else "failure"
            self.log_operation(
                "QUERY_COURSE_ASSIGNMENTS",
                status,
                time.time() - start_time,
                {"course_id": course_id},
                str(error),
            )

    def create_assignment_operation(self, course_id: str) -> str | None:
        start_time = time.time()
        try:
            assignment_name = f"Stress Assignment T{self.thread_id} {uuid.uuid4().hex[:8]}"
            assignment_id = create_assignment(assignment_name, course_id)
            remember_created("assignments", assignment_id)
            add_active("assignments", assignment_id)
            self.log_operation(
                "CREATE_ASSIGNMENT",
                "success",
                time.time() - start_time,
                {
                    "assignment_id": assignment_id,
                    "course_id": course_id,
                    "name": assignment_name,
                },
            )
            return assignment_id
        except Exception as error:
            status = "conflict" if is_expected_race(error) else "failure"
            self.log_operation(
                "CREATE_ASSIGNMENT",
                status,
                time.time() - start_time,
                {"course_id": course_id},
                str(error),
            )
            return None

    def delete_assignment_operation(self, assignment_id: str) -> bool:
        start_time = time.time()
        try:
            delete_assignment(assignment_id)
            remove_active("assignments", assignment_id)
            self.log_operation(
                "DELETE_ASSIGNMENT",
                "success",
                time.time() - start_time,
                {"assignment_id": assignment_id},
            )
            return True
        except Exception as error:
            status = "conflict" if is_expected_race(error) else "failure"
            self.log_operation(
                "DELETE_ASSIGNMENT",
                status,
                time.time() - start_time,
                {"assignment_id": assignment_id},
                str(error),
            )
            return False

    def query_assignment_operation(self, assignment_id: str) -> None:
        start_time = time.time()
        try:
            assignment_data = get_assignment(assignment_id)
            self.log_operation(
                "QUERY_ASSIGNMENT",
                "success",
                time.time() - start_time,
                {
                    "assignment_id": assignment_id,
                    "name": assignment_data.get("name") if assignment_data else None,
                },
            )
        except Exception as error:
            status = "conflict" if is_expected_race(error) else "failure"
            self.log_operation(
                "QUERY_ASSIGNMENT",
                status,
                time.time() - start_time,
                {"assignment_id": assignment_id},
                str(error),
            )

    def skip_operation(self, operation_type: str, reason: str) -> None:
        self.log_operation(operation_type, "skipped", 0, {"reason": reason})


def store_result(thread_id: int, test_type: str, operations_count: int, tester: ConcurrentCRUDTester) -> dict:
    result = {
        "thread_id": thread_id,
        "test_type": test_type,
        "total_operations": operations_count,
        "successful_operations": tester.successful_operations,
        "handled_conflicts": tester.handled_conflicts,
        "skipped_operations": tester.skipped_operations,
        "failed_operations": tester.failed_operations,
        "operations": tester.operations,
        "errors": tester.errors,
    }

    with results_lock:
        test_results.append(result)

    handled = (
        tester.successful_operations
        + tester.handled_conflicts
        + tester.skipped_operations
    )
    print(f"[thread {thread_id}] completed {handled}/{operations_count} handled")
    return result


def run_course_crud_operations(thread_id: int, operations_count: int, instructor_id: str) -> dict:
    tester = ConcurrentCRUDTester(thread_id, instructor_id)
    local_courses = []
    print(f"[thread {thread_id}] starting {operations_count} course CRUD operations")

    for _ in range(operations_count):
        if not local_courses or random.random() < 0.45:
            course_id = tester.create_course_operation()
            if course_id:
                local_courses.append(course_id)
        elif random.random() < 0.3:
            course_id = random.choice(local_courses)
            if tester.delete_course_operation(course_id):
                local_courses.remove(course_id)
        else:
            available_courses = get_active("courses")
            if not available_courses:
                tester.skip_operation("QUERY_COURSE", "no active courses")
            else:
                course_id = random.choice(available_courses)
                if random.choice([True, False]):
                    tester.query_course_operation(course_id)
                else:
                    tester.query_course_assignments_operation(course_id)

        time.sleep(random.uniform(0.01, 0.08))

    return store_result(thread_id, "course_crud", operations_count, tester)


def run_assignment_crud_operations(thread_id: int, operations_count: int, instructor_id: str) -> dict:
    tester = ConcurrentCRUDTester(thread_id, instructor_id)
    local_assignments = []
    print(f"[thread {thread_id}] starting {operations_count} assignment CRUD operations")

    initial_course = tester.create_course_operation()
    if not initial_course:
        tester.skip_operation("ASSIGNMENT_CRUD", "could not create initial course")
        return store_result(thread_id, "assignment_crud", operations_count, tester)

    for _ in range(operations_count):
        available_courses = get_active("courses")
        if not available_courses:
            course_id = tester.create_course_operation()
            if course_id:
                available_courses = [course_id]

        if not available_courses:
            tester.skip_operation("CREATE_ASSIGNMENT", "no active courses")
            continue

        if not local_assignments or random.random() < 0.45:
            assignment_id = tester.create_assignment_operation(random.choice(available_courses))
            if assignment_id:
                local_assignments.append(assignment_id)
        elif random.random() < 0.3:
            assignment_id = random.choice(local_assignments)
            if tester.delete_assignment_operation(assignment_id):
                local_assignments.remove(assignment_id)
        else:
            available_assignments = get_active("assignments")
            if not available_assignments:
                tester.skip_operation("QUERY_ASSIGNMENT", "no active assignments")
            else:
                tester.query_assignment_operation(random.choice(available_assignments))

        time.sleep(random.uniform(0.01, 0.08))

    return store_result(thread_id, "assignment_crud", operations_count, tester)


def run_mixed_crud_operations(thread_id: int, operations_count: int, instructor_id: str) -> dict:
    tester = ConcurrentCRUDTester(thread_id, instructor_id)
    local_courses = []
    local_assignments = []
    print(f"[thread {thread_id}] starting {operations_count} mixed CRUD operations")

    for _ in range(operations_count):
        available_courses = get_active("courses")

        if not available_courses or random.random() < 0.35:
            course_id = tester.create_course_operation()
            if course_id:
                local_courses.append(course_id)
        elif random.random() < 0.25 and local_assignments:
            assignment_id = random.choice(local_assignments)
            if tester.delete_assignment_operation(assignment_id):
                local_assignments.remove(assignment_id)
        elif random.random() < 0.2 and local_courses:
            course_id = random.choice(local_courses)
            if tester.delete_course_operation(course_id):
                local_courses.remove(course_id)
        elif random.random() < 0.5:
            assignment_id = tester.create_assignment_operation(random.choice(available_courses))
            if assignment_id:
                local_assignments.append(assignment_id)
        else:
            available_assignments = get_active("assignments")
            if available_assignments and random.choice([True, False]):
                tester.query_assignment_operation(random.choice(available_assignments))
            elif available_courses:
                tester.query_course_operation(random.choice(available_courses))
            else:
                tester.skip_operation("QUERY_RESOURCE", "no active resources")

        time.sleep(random.uniform(0.01, 0.08))

    return store_result(thread_id, "mixed_crud", operations_count, tester)


def print_results_summary() -> None:
    print()
    print("=" * 80)
    print("CONCURRENT CRUD OPERATIONS STRESS TEST RESULTS")
    print("=" * 80)

    total_threads = len(test_results)
    total_operations = sum(result["total_operations"] for result in test_results)
    total_successful = sum(result["successful_operations"] for result in test_results)
    total_conflicts = sum(result["handled_conflicts"] for result in test_results)
    total_skipped = sum(result["skipped_operations"] for result in test_results)
    total_failed = sum(result["failed_operations"] for result in test_results)
    handled = total_successful + total_conflicts + total_skipped
    handled_rate = (handled / total_operations * 100) if total_operations else 0

    print(f"Total threads: {total_threads}")
    print(f"Total requested operations: {total_operations}")
    print(f"Successful operations: {total_successful}")
    print(f"Handled conflicts/races: {total_conflicts}")
    print(f"Skipped operations: {total_skipped}")
    print(f"Unexpected failures: {total_failed}")
    print(f"Handled rate: {handled_rate:.1f}%")
    print()

    operation_stats = {}
    durations = []
    for result in test_results:
        for operation in result["operations"]:
            op_type = operation["type"]
            status = operation["status"]
            durations.append(operation["duration"])
            operation_stats.setdefault(
                op_type,
                {"total": 0, "success": 0, "conflict": 0, "skipped": 0, "failure": 0},
            )
            operation_stats[op_type]["total"] += 1
            operation_stats[op_type][status] += 1

    if operation_stats:
        print("Operation summary:")
        print(
            f"{'Operation':<26} {'Total':>6} {'Pass':>6} "
            f"{'Conflict':>9} {'Skip':>6} {'Fail':>6}"
        )
        print("-" * 65)
        for op_type, stats in sorted(operation_stats.items()):
            print(
                f"{op_type:<26} {stats['total']:>6} {stats['success']:>6} "
                f"{stats['conflict']:>9} {stats['skipped']:>6} {stats['failure']:>6}"
            )
        print()

    if durations:
        nonzero = [duration for duration in durations if duration > 0]
        if nonzero:
            print("Performance:")
            print(f"- Average operation time: {sum(nonzero) / len(nonzero):.3f}s")
            print(f"- Fastest operation: {min(nonzero):.3f}s")
            print(f"- Slowest operation: {max(nonzero):.3f}s")
            print()

    print("Resource summary:")
    print(f"- Courses created: {len(created_courses)}")
    print(f"- Assignments created: {len(created_assignments)}")
    print(f"- Active courses remaining before cleanup: {len(get_active('courses'))}")
    print(f"- Active assignments remaining before cleanup: {len(get_active('assignments'))}")

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

    deleted_assignments = 0
    for assignment_id in reversed(created_assignments):
        try:
            delete_assignment(assignment_id)
            deleted_assignments += 1
            remove_active("assignments", assignment_id)
        except Exception as error:
            if not is_expected_race(error):
                print(f"- Failed to delete assignment {assignment_id}: {error}")

    deleted_courses = 0
    for course_id in reversed(created_courses):
        try:
            delete_course(course_id)
            deleted_courses += 1
            remove_active("courses", course_id)
        except Exception as error:
            if not is_expected_race(error):
                print(f"- Failed to delete course {course_id}: {error}")

    deleted_users = 0
    for user_id in created_users:
        try:
            delete_user(user_id)
            deleted_users += 1
        except Exception as error:
            print(f"- Failed to delete user {user_id}: {error}")

    print(f"- Deleted assignments: {deleted_assignments}/{len(created_assignments)}")
    print(f"- Deleted courses: {deleted_courses}/{len(created_courses)}")
    print(f"- Deleted users: {deleted_users}/{len(created_users)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Concurrent CRUD operations stress test.")
    parser.add_argument("--num_threads", type=int, default=6, help="Number of threads")
    parser.add_argument(
        "--operations_per_thread",
        type=int,
        default=15,
        help="Number of operations per thread",
    )
    parser.add_argument(
        "--test_type",
        choices=["courses", "assignments", "mixed", "both"],
        default="both",
        help="Type of CRUD operations to run",
    )
    parser.add_argument(
        "--max_workers",
        type=int,
        default=10,
        help="Maximum concurrent workers",
    )
    parser.add_argument("--cleanup", action="store_true", help="Delete created resources")

    args = parser.parse_args()

    if args.num_threads < 1 or args.operations_per_thread < 1 or args.max_workers < 1:
        print("Failed to run stress test: thread, operation, and worker counts must be >= 1")
        return 1

    print("Starting concurrent CRUD operations stress test")
    print(f"Threads: {args.num_threads}")
    print(f"Operations per thread: {args.operations_per_thread}")
    print(f"Test type: {args.test_type}")
    print(f"Max workers: {args.max_workers}")

    try:
        instructor_id = add_user(
            name=f"crud_instructor_{uuid.uuid4().hex[:8]}",
            role="Instructor",
        )
        remember_created("users", instructor_id)
        print(f"Created test instructor: {instructor_id}")

        tasks = []
        if args.test_type in ["courses", "both"]:
            thread_count = args.num_threads if args.test_type == "courses" else args.num_threads // 2
            for index in range(thread_count):
                tasks.append((run_course_crud_operations, index, args.operations_per_thread))

        if args.test_type in ["assignments", "both"]:
            start_id = 0 if args.test_type == "assignments" else args.num_threads // 2
            thread_count = (
                args.num_threads
                if args.test_type == "assignments"
                else args.num_threads - args.num_threads // 2
            )
            for index in range(thread_count):
                tasks.append(
                    (run_assignment_crud_operations, start_id + index, args.operations_per_thread)
                )

        if args.test_type == "mixed":
            for index in range(args.num_threads):
                tasks.append((run_mixed_crud_operations, index, args.operations_per_thread))

        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = [
                executor.submit(func, thread_id, operations_count, instructor_id)
                for func, thread_id, operations_count in tasks
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
            print("Failed to run stress test: unexpected CRUD failures occurred")
            return 1

        return 0

    except Exception as error:
        print(f"Failed to run stress test: {error}")
        if args.cleanup:
            cleanup()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
