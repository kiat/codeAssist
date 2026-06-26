import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


"""
Comprehensive stress test runner that executes stress tests in sequence.

This script runs backend stress tests and provides a consolidated report.

Usage:
    python run_all_stress_tests.py <course_id> [--quick] [--cleanup]

Examples:
    python run_all_stress_tests.py 123e4567-e89b-12d3-a456-426614174000 --quick --cleanup
    python backend/test/stress/run_all_stress_tests.py 123e4567-e89b-12d3-a456-426614174000 --quick --cleanup
"""


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "results"
DEFAULT_TIMEOUT_SECONDS = 600


def output_has_failure(output: str) -> bool:
    """
    Some older stress scripts return exit code 0 even when the actual test failed.
    This helper scans stdout/stderr for known failure markers.
    """
    failure_markers = (
        "Test failed:",
        "Failed to run stress test:",
        "Error uploading submission:",
        "] Error:",
        "Thread failed with exception:",
        "Task failed with exception:",
        "Traceback",
        "500 Server Error",
        "400 Client Error",
        "404 Client Error",
        "BAD REQUEST",
        "NOT FOUND",
        "Successful operations: 0",
        "Successful: 0",
        "Failed operations: 1",
    )
    return any(marker in output for marker in failure_markers)


class StressTestRunner:
    def __init__(
        self,
        course_id: str,
        quick_mode: bool = False,
        cleanup: bool = True,
        base_url: str = "http://localhost:5001",
    ):
        self.course_id = course_id
        self.quick_mode = quick_mode
        self.cleanup = cleanup
        self.base_url = base_url
        self.test_results = []
        self.start_time = None
        self.end_time = None

    def build_command(self, script_path: str, args: list[str], command_shape: str) -> list[str]:
        script_file = str(SCRIPT_DIR / script_path)

        if command_shape == "course_first":
            return [sys.executable, script_file, self.course_id] + args

        if command_shape == "threads_first":
            return [sys.executable, script_file] + args

        if command_shape == "no_course":
            return [sys.executable, script_file] + args

        raise ValueError(f"Unknown command shape: {command_shape}")

    def run_test(
        self,
        test_name: str,
        script_path: str,
        args: list[str],
        command_shape: str = "course_first",
        supports_cleanup: bool = True,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> bool:
        """Run a single stress test and capture results."""
        print()
        print("=" * 60)
        print(f"Running {test_name}")
        print("=" * 60)

        cmd = self.build_command(script_path, args, command_shape)

        if self.cleanup and supports_cleanup:
            cmd.append("--cleanup")

        print(f"Command: {' '.join(cmd)}")
        print()

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["STRESS_BASE_URL"] = self.base_url

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                cwd=SCRIPT_DIR,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout_seconds,
                env=env,
            )

            duration = time.time() - start_time
            combined_output = f"{result.stdout}\n{result.stderr}"
            success = result.returncode == 0 and not output_has_failure(combined_output)

            test_result = {
                "test_name": test_name,
                "script_path": script_path,
                "duration": duration,
                "success": success,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd),
                "command_shape": command_shape,
                "supports_cleanup": supports_cleanup,
            }

            self.test_results.append(test_result)

            if success:
                print(f"PASS {test_name} completed successfully in {duration:.2f}s")
            else:
                print(f"FAIL {test_name} failed after {duration:.2f}s")
                print(f"Return code: {result.returncode}")

                if result.stderr:
                    print()
                    print("STDERR:")
                    print(result.stderr[-2000:])

                if result.stdout:
                    print()
                    print("STDOUT tail:")
                    print(result.stdout[-3000:])

            if success and result.stdout:
                print(result.stdout)

            return success

        except subprocess.TimeoutExpired as error:
            duration = time.time() - start_time

            print(f"TIMEOUT {test_name} timed out after {duration:.2f}s")

            test_result = {
                "test_name": test_name,
                "script_path": script_path,
                "duration": duration,
                "success": False,
                "return_code": -1,
                "stdout": error.stdout or "",
                "stderr": f"Test timed out after {timeout_seconds} seconds",
                "command": " ".join(cmd),
                "command_shape": command_shape,
                "supports_cleanup": supports_cleanup,
            }

            self.test_results.append(test_result)
            return False

        except Exception as error:
            duration = time.time() - start_time

            print(f"CRASH {test_name} crashed: {error}")

            test_result = {
                "test_name": test_name,
                "script_path": script_path,
                "duration": duration,
                "success": False,
                "return_code": -2,
                "stdout": "",
                "stderr": str(error),
                "command": " ".join(cmd),
                "command_shape": command_shape,
                "supports_cleanup": supports_cleanup,
            }

            self.test_results.append(test_result)
            return False

    def get_test_configs(self) -> list[tuple]:
        """
        Return test configurations.

        Tuple format:
            (
                test_name,
                script_path,
                args,
                command_shape,
                supports_cleanup,
                timeout_seconds,
            )
        """
        if self.quick_mode:
            return [
                (
                    "Bulk Assignment Uploads",
                    "test_bulk_assignment_uploads.py",
                    ["--num_uploads", "2", "--max_workers", "1"],
                    "course_first",
                    True,
                    600,
                ),
                (
                    "Student Submissions",
                    "upload_assignments.py",
                    ["--num_threads", "1"],
                    "course_first",
                    True,
                    600,
                ),
                (
                    "Assignment Creation",
                    "create_assignments.py",
                    ["1", self.course_id],
                    "threads_first",
                    False,
                    600,
                ),
                (
                    "Long-Running Grader",
                    "test_long_running_grader.py",
                    [
                        "--max_execution_time",
                        "1",
                        "--num_submissions",
                        "1",
                        "--max_workers",
                        "1",
                    ],
                    "course_first",
                    True,
                    600,
                ),
                (
                    "Concurrent Enrollment",
                    "test_concurrent_enrollment.py",
                    [
                        "--num_threads",
                        "1",
                        "--operations_per_thread",
                        "2",
                        "--max_workers",
                        "1",
                    ],
                    "course_first",
                    True,
                    600,
                ),
                (
                    "CRUD Operations",
                    "test_concurrent_crud_operations.py",
                    [
                        "--num_threads",
                        "1",
                        "--operations_per_thread",
                        "1",
                        "--test_type",
                        "mixed",
                        "--max_workers",
                        "1",
                    ],
                    "no_course",
                    True,
                    600,
                ),
            ]

        return [
            (
                "Bulk Assignment Uploads",
                "test_bulk_assignment_uploads.py",
                ["--num_uploads", "25", "--max_workers", "8", "--monitor_system"],
                "course_first",
                True,
                900,
            ),
            (
                "Student Submissions",
                "upload_assignments.py",
                ["--num_threads", "10"],
                "course_first",
                True,
                900,
            ),
            (
                "Assignment Creation",
                "create_assignments.py",
                ["10", self.course_id],
                "threads_first",
                False,
                900,
            ),
            (
                "Long-Running Grader",
                "test_long_running_grader.py",
                [
                    "--max_execution_time",
                    "20",
                    "--num_submissions",
                    "3",
                    "--max_workers",
                    "5",
                ],
                "course_first",
                True,
                900,
            ),
                (
                    "Concurrent Enrollment",
                    "test_concurrent_enrollment.py",
                    [
                        "--num_threads",
                        "5",
                        "--operations_per_thread",
                        "10",
                        "--max_workers",
                        "5",
                    ],
                    "course_first",
                    True,
                    900,
            ),
            (
                "CRUD Operations (Courses)",
                "test_concurrent_crud_operations.py",
                [
                    "--num_threads",
                    "6",
                    "--operations_per_thread",
                    "15",
                        "--test_type",
                        "courses",
                        "--max_workers",
                        "6",
                    ],
                    "no_course",
                    True,
                900,
            ),
            (
                "CRUD Operations (Assignments)",
                "test_concurrent_crud_operations.py",
                [
                    "--num_threads",
                    "6",
                    "--operations_per_thread",
                    "15",
                        "--test_type",
                        "assignments",
                        "--max_workers",
                        "6",
                    ],
                    "no_course",
                    True,
                900,
            ),
            (
                "CRUD Operations (Mixed)",
                "test_concurrent_crud_operations.py",
                [
                    "--num_threads",
                    "8",
                    "--operations_per_thread",
                    "12",
                        "--test_type",
                        "mixed",
                        "--max_workers",
                        "8",
                    ],
                    "no_course",
                    True,
                900,
            ),
        ]

    def run_all_tests(self) -> None:
        """Run all configured stress tests in sequence."""
        self.start_time = time.time()

        print("Starting comprehensive stress test suite")
        print(f"Course ID: {self.course_id}")
        print(f"Backend URL: {self.base_url}")
        print(f"Quick mode: {self.quick_mode}")
        print(f"Cleanup enabled: {self.cleanup}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        test_configs = self.get_test_configs()

        for index, (
            test_name,
            script_path,
            args,
            command_shape,
            supports_cleanup,
            timeout_seconds,
        ) in enumerate(test_configs, start=1):
            print()
            print(f"[{index}/{len(test_configs)}] {test_name}")
            self.run_test(
                test_name=test_name,
                script_path=script_path,
                args=args,
                command_shape=command_shape,
                supports_cleanup=supports_cleanup,
                timeout_seconds=timeout_seconds,
            )

            time.sleep(2)

        self.end_time = time.time()
        self.print_summary()
        self.save_results()

    def print_summary(self) -> None:
        """Print a comprehensive summary of all test results."""
        total_duration = self.end_time - self.start_time
        successful_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = len(self.test_results) - successful_tests

        print()
        print("=" * 80)
        print("COMPREHENSIVE STRESS TEST RESULTS SUMMARY")
        print("=" * 80)
        print(f"Test Suite Duration: {total_duration:.2f}s ({total_duration / 60:.1f} minutes)")
        print(f"Total Tests: {len(self.test_results)}")

        if self.test_results:
            success_rate = successful_tests / len(self.test_results) * 100
            failure_rate = failed_tests / len(self.test_results) * 100
        else:
            success_rate = 0
            failure_rate = 0

        print(f"Successful Tests: {successful_tests} ({success_rate:.1f}%)")
        print(f"Failed Tests: {failed_tests} ({failure_rate:.1f}%)")
        print()

        print("INDIVIDUAL TEST RESULTS:")
        print("-" * 60)

        for result in self.test_results:
            status = "PASS" if result["success"] else "FAIL"
            duration = result["duration"]
            print(f"  {status:<4} | {result['test_name']:<30} | {duration:6.2f}s")

        print()

        if failed_tests > 0:
            print("FAILED TEST DETAILS:")
            print("-" * 60)

            for result in self.test_results:
                if not result["success"]:
                    print(f"  {result['test_name']}:")
                    print(f"    Return Code: {result['return_code']}")

                    stderr = result.get("stderr") or ""
                    stdout = result.get("stdout") or ""

                    if stderr:
                        print(f"    Error: {stderr[:500]}...")

                    if stdout:
                        print(f"    Output: {stdout[:500]}...")

                    print()

        test_durations = [
            result["duration"] for result in self.test_results if result["success"]
        ]

        if test_durations:
            avg_duration = sum(test_durations) / len(test_durations)
            max_duration = max(test_durations)
            min_duration = min(test_durations)

            print("PERFORMANCE SUMMARY:")
            print(f"  Average test duration: {avg_duration:.2f}s")
            print(f"  Longest test: {max_duration:.2f}s")
            print(f"  Shortest test: {min_duration:.2f}s")
            print()

        print("OVERALL ASSESSMENT:")

        if successful_tests == len(self.test_results):
            print("  All stress tests passed.")
        elif successful_tests >= len(self.test_results) * 0.8:
            print("  Most tests passed, but some issues were detected.")
        else:
            print(
                "  Multiple test failures were detected. "
                "Review failed tests before treating this as a performance issue."
            )

        print()
        print("=" * 80)

    def save_results(self) -> None:
        """Save detailed test results to a JSON file."""
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = RESULTS_DIR / f"stress_test_results_{timestamp}.json"

        results_data = {
            "test_suite_info": {
                "course_id": self.course_id,
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "end_time": datetime.fromtimestamp(self.end_time).isoformat(),
                "total_duration": self.end_time - self.start_time,
                "quick_mode": self.quick_mode,
                "cleanup_enabled": self.cleanup,
                "base_url": self.base_url,
            },
            "summary": {
                "total_tests": len(self.test_results),
                "successful_tests": sum(
                    1 for result in self.test_results if result["success"]
                ),
                "failed_tests": sum(
                    1 for result in self.test_results if not result["success"]
                ),
            },
            "test_results": self.test_results,
        }

        try:
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(results_data, file, indent=2)

            print(f"Detailed results saved to: {filename}")

        except Exception as error:
            print(f"Failed to save results file: {error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Comprehensive stress test runner.")
    parser.add_argument("course_id", type=str, help="Valid course ID for all tests")
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run all tests with reduced baseline load for faster execution",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        default=True,
        help="Clean up created resources after each test. Default: enabled.",
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_false",
        dest="cleanup",
        help="Do not clean up created resources",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("STRESS_BASE_URL", "http://localhost:5001"),
        help="Backend URL. Default: http://localhost:5001",
    )
    return parser.parse_args()


def validate_course_id(course_id: str) -> str:
    cleaned = course_id.strip()
    if not cleaned or cleaned in {"<course_id>", "course_id", "COURSE_ID"}:
        raise ValueError("Replace COURSE_ID with a real course id. Do not type angle brackets.")
    if cleaned.startswith("<") or cleaned.endswith(">"):
        raise ValueError("Replace COURSE_ID with a real course id. Do not type angle brackets.")
    return cleaned


def check_required_scripts() -> bool:
    required_scripts = [
        "test_bulk_assignment_uploads.py",
        "upload_assignments.py",
        "create_assignments.py",
        "test_long_running_grader.py",
        "test_concurrent_enrollment.py",
        "test_concurrent_crud_operations.py",
        "utils.py",
    ]

    missing_scripts = []

    for script in required_scripts:
        if not (SCRIPT_DIR / script).exists():
            missing_scripts.append(script)

    if missing_scripts:
        print("Missing required test scripts:")

        for script in missing_scripts:
            print(f"   - {script}")

        print()
        print("Please ensure all stress test scripts are in backend/test/stress.")
        return False

    return True


def main() -> int:
    args = parse_args()

    try:
        course_id = validate_course_id(args.course_id)
    except ValueError as error:
        print(f"ERROR: {error}")
        return 2

    if not check_required_scripts():
        return 1

    runner = StressTestRunner(
        course_id=course_id,
        quick_mode=args.quick,
        cleanup=args.cleanup,
        base_url=args.base_url,
    )
    runner.run_all_tests()

    failed_tests = sum(1 for result in runner.test_results if not result["success"])
    return 0 if failed_tests == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
