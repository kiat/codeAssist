"""
Local stress-test entrypoint for the current backend.

This wrapper keeps the original stress scripts intact, but gives local users a
safer way to check prerequisites, preview commands, and run only scripts whose
CLI shape matches the current backend branch.
"""

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import NamedTuple
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
USE_COLOR = os.environ.get("NO_COLOR") is None


class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def color(text: str, code: str) -> str:
    if not USE_COLOR:
        return text
    return f"{code}{text}{Color.RESET}"


def status_label(success: bool) -> str:
    if success:
        return color("PASS", Color.GREEN + Color.BOLD)
    return color("FAIL", Color.RED + Color.BOLD)


def print_section(title: str) -> None:
    line = "=" * 72
    print()
    print(color(line, Color.CYAN))
    print(color(title, Color.CYAN + Color.BOLD))
    print(color(line, Color.CYAN))


def progress_bar(current: int, total: int, width: int = 24) -> str:
    filled = int(width * current / total)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {current}/{total}"

SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "results"
DEFAULT_BASE_URL = "http://localhost:5001"


class StressCase(NamedTuple):
    name: str
    script: str
    description: str
    status: str
    reason: str
    command_shape: str
    quick_args: tuple[str, ...]
    full_args: tuple[str, ...]
    timeout_seconds: int = 600


TEST_CASES = (
    StressCase(
        name="bulk_uploads",
        script="test_bulk_assignment_uploads.py",
        description="Create assignments and upload autograder zips concurrently.",
        status="safe",
        reason="Uses current /create_assignment and /upload_assignment_autograder endpoints.",
        command_shape="course_first",
        quick_args=("--num_uploads", "2", "--max_workers", "1", "--cleanup"),
        full_args=("--num_uploads", "10", "--max_workers", "4", "--cleanup"),
    ),
    StressCase(
        name="student_submissions",
        script="upload_assignments.py",
        description="Create one assignment and submit as multiple students.",
        status="safe",
        reason="Uses current assignment, autograder, user, and submission endpoints.",
        command_shape="course_first",
        quick_args=("--num_threads", "2", "--cleanup"),
        full_args=("--num_threads", "5", "--cleanup"),
    ),
    StressCase(
        name="assignment_creation",
        script="create_assignments.py",
        description="Create assignments and upload autograders from multiple threads.",
        status="safe",
        reason="Uses a different argument order, handled by this runner.",
        command_shape="threads_first",
        quick_args=("2",),
        full_args=("5",),
    ),
    StressCase(
        name="long_running_grader",
        script="test_long_running_grader.py",
        description="Submit code that sleeps or burns CPU before grading completes.",
        status="manual",
        reason="Runs slowly and currently sleeps instead of polling real grading state.",
        command_shape="course_first",
        quick_args=(
            "--max_execution_time",
            "1",
            "--num_submissions",
            "1",
            "--max_workers",
            "1",
            "--cleanup",
        ),
        full_args=(
            "--max_execution_time",
            "10",
            "--num_submissions",
            "1",
            "--max_workers",
            "2",
            "--cleanup",
        ),
        timeout_seconds=900,
    ),
    StressCase(
        name="concurrent_enrollment",
        script="test_concurrent_enrollment.py",
        description="Rapidly enroll and unenroll users.",
        status="incompatible",
        reason="Calls /enroll_user, /unenroll_user, and /get_user_courses, which this backend does not expose.",
        command_shape="course_first",
        quick_args=("--num_threads", "2", "--operations_per_thread", "3", "--cleanup"),
        full_args=("--num_threads", "5", "--operations_per_thread", "10", "--cleanup"),
    ),
    StressCase(
        name="crud_operations",
        script="test_concurrent_crud_operations.py",
        description="Create, query, and delete courses and assignments concurrently.",
        status="incompatible",
        reason="Creates courses without semester/year/entryCode and calls /get_course instead of /get_course_info.",
        command_shape="no_course",
        quick_args=(
            "--num_threads",
            "2",
            "--operations_per_thread",
            "3",
            "--test_type",
            "mixed",
            "--cleanup",
        ),
        full_args=(
            "--num_threads",
            "6",
            "--operations_per_thread",
            "15",
            "--test_type",
            "mixed",
            "--cleanup",
        ),
    ),
)


def get_case(name: str) -> StressCase:
    for case in TEST_CASES:
        if case.name == name:
            return case
    raise KeyError(f"Unknown stress case: {name}")


def normalize_course_id(course_id: str | None, required: bool) -> str | None:
    if course_id is None or course_id.strip() == "":
        if required:
            raise ValueError("Replace COURSE_ID with a real course id before running tests.")
        return None

    cleaned = course_id.strip()
    if cleaned in {"<course_id>", "course_id", "COURSE_ID"}:
        raise ValueError("Replace COURSE_ID with a real course id. Do not type angle brackets.")

    if cleaned.startswith("<") or cleaned.endswith(">"):
        raise ValueError("Replace COURSE_ID with a real course id. Do not type angle brackets.")

    return cleaned


def select_cases(
    run_safe: bool,
    include_manual: bool = False,
    include_incompatible: bool = False,
    only: list[str] | None = None,
) -> list[StressCase]:
    selected = []
    requested = set(only or [])

    for case in TEST_CASES:
        if requested and case.name not in requested:
            continue
        if run_safe:
            if case.status == "safe":
                selected.append(case)
            elif include_manual and case.status == "manual":
                selected.append(case)
            elif include_incompatible and case.status == "incompatible":
                selected.append(case)
        else:
            selected.append(case)

    return selected


def build_command(
    case: StressCase,
    course_id: str | None,
    quick: bool,
    script_dir: Path = SCRIPT_DIR,
) -> list[str]:
    script_path = script_dir / case.script
    args = list(case.quick_args if quick else case.full_args)

    if case.command_shape == "course_first":
        if not course_id:
            raise ValueError(f"{case.name} needs a course id")
        return [sys.executable, str(script_path), course_id] + args

    if case.command_shape == "threads_first":
        if not course_id:
            raise ValueError(f"{case.name} needs a course id")
        if not args:
            raise ValueError(f"{case.name} is missing thread-count arguments")
        return [sys.executable, str(script_path), args[0], course_id] + args[1:]

    if case.command_shape == "no_course":
        return [sys.executable, str(script_path)] + args

    raise ValueError(f"Unknown command shape for {case.name}: {case.command_shape}")


def format_command(command: list[str]) -> str:
    parts = []
    for item in command:
        if " " in item:
            parts.append(f'"{item}"')
        else:
            parts.append(item)
    return " ".join(parts)


def package_status(package_name: str) -> str:
    return "installed" if importlib.util.find_spec(package_name) else "missing"


def server_status(base_url: str) -> str:
    try:
        with urlopen(base_url, timeout=2) as response:
            return f"reachable: HTTP {response.status}"
    except HTTPError as error:
        return f"reachable: HTTP {error.code}"
    except URLError as error:
        return f"not reachable: {error.reason}"
    except Exception as error:
        return f"not reachable: {error}"


def script_status(case: StressCase, script_dir: Path = SCRIPT_DIR) -> str:
    return "found" if (script_dir / case.script).exists() else "missing"


def output_has_failure(output: str) -> bool:
    failure_markers = (
        "Test failed:",
        "Failed to run stress test:",
        "Error uploading submission:",
        "] Error:",
        "Thread failed with exception:",
        "Task failed with exception:",
    )
    return any(marker in output for marker in failure_markers)


def run_case(
    case: StressCase,
    course_id: str,
    quick: bool,
    base_url: str,
    script_dir: Path = SCRIPT_DIR,
) -> dict:
    command = build_command(case, course_id=course_id, quick=quick, script_dir=script_dir)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    env["STRESS_BASE_URL"] = base_url

    start = time.time()
    try:
        result = subprocess.run(
            command,
            cwd=script_dir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=case.timeout_seconds,
            env=env,
        )
        duration = time.time() - start
        combined_output = f"{result.stdout}\n{result.stderr}"
        success = result.returncode == 0 and not output_has_failure(combined_output)
        return {
            "name": case.name,
            "script": case.script,
            "command": command,
            "command_display": format_command(command),
            "return_code": result.returncode,
            "duration_seconds": duration,
            "success": success,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired as error:
        return {
            "name": case.name,
            "script": case.script,
            "command": command,
            "command_display": format_command(command),
            "return_code": -1,
            "duration_seconds": time.time() - start,
            "success": False,
            "stdout": error.stdout or "",
            "stderr": f"Timed out after {case.timeout_seconds} seconds",
        }


def save_results(results: list[dict], base_url: str, quick: bool) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_path = RESULTS_DIR / f"local_stress_results_{timestamp}.json"
    payload = {
        "created_at": datetime.now().isoformat(),
        "base_url": base_url,
        "quick": quick,
        "summary": {
            "total": len(results),
            "passed": sum(1 for result in results if result["success"]),
            "failed": sum(1 for result in results if not result["success"]),
        },
        "results": results,
    }
    result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return result_path


def print_preflight(cases: list[StressCase], base_url: str, check_server: bool) -> None:
    print_section("Local stress test preflight")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Stress folder: {SCRIPT_DIR}")
    print(f"Backend URL: {base_url}")
    print(f"requests: {package_status('requests')}")
    print(f"psutil: {package_status('psutil')}")
    if check_server:
        print(f"Backend server: {server_status(base_url)}")
    print()
    print("Cases:")
    for case in cases:
        case_status = case.status
        if case.status == "safe":
            case_status = color(case.status, Color.GREEN + Color.BOLD)
        elif case.status == "manual":
            case_status = color(case.status, Color.YELLOW + Color.BOLD)
        elif case.status == "incompatible":
            case_status = color(case.status, Color.RED + Color.BOLD)

        found_status = script_status(case)
        if found_status == "found":
            found_status = color(found_status, Color.GREEN)
        else:
            found_status = color(found_status, Color.RED)

        print(f"- {case.name}: {case_status}; script {found_status}")
        print(f"  {case.reason}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or run local backend stress tests safely."
    )
    parser.add_argument(
        "course_id",
        nargs="?",
        help="Real course id. Do not type <course_id>.",
    )
    parser.add_argument(
        "--course-id",
        dest="course_id_flag",
        help="Real course id, alternative to the positional argument.",
    )
    parser.add_argument(
        "--run-safe",
        action="store_true",
        help="Run only stress cases marked safe for this backend.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview commands only. This is the default when --run-safe is omitted.",
    )
    parser.add_argument(
        "--include-manual",
        action="store_true",
        help="Also run manual cases such as long_running_grader.",
    )
    parser.add_argument(
        "--include-incompatible",
        action="store_true",
        help="Also run known incompatible cases. Usually only useful while fixing them.",
    )
    parser.add_argument(
        "--only",
        action="append",
        choices=[case.name for case in TEST_CASES],
        help="Run or preview one named case. Can be repeated.",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Use larger local arguments instead of quick smoke-test arguments.",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("STRESS_BASE_URL", DEFAULT_BASE_URL),
        help=f"Backend URL. Default: {DEFAULT_BASE_URL}",
    )
    parser.add_argument(
        "--check-server",
        action="store_true",
        help="Try a quick connection to the backend URL during preflight.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    quick = not args.full
    raw_course_id = args.course_id_flag or args.course_id

    try:
        course_id = normalize_course_id(raw_course_id, required=args.run_safe)
    except ValueError as error:
        print(f"ERROR: {error}")
        return 2

    cases = select_cases(
        run_safe=args.run_safe,
        include_manual=args.include_manual,
        include_incompatible=args.include_incompatible,
        only=args.only,
    )

    print_preflight(cases, base_url=args.base_url, check_server=args.check_server)
    print()

    if not args.run_safe:
        print("Dry run only. No stress scripts were executed.")
        print("Command preview:")
        preview_course_id = course_id or "COURSE_ID"
        for case in cases:
            try:
                command = build_command(case, preview_course_id, quick=quick)
                print(f"- {case.name}: {format_command(command)}")
            except ValueError as error:
                print(f"- {case.name}: cannot preview command: {error}")
        print()
        print("To run safe tests, use:")
        print("  python backend/test/stress/run_local_stress_tests.py COURSE_ID --run-safe")
        return 0

    if not course_id:
        print("ERROR: Replace COURSE_ID with a real course id.")
        return 2

    print_section("Running selected stress cases")
    results = []
    total_cases = len(cases)

    for index, case in enumerate(cases, start=1):
        print()
        print(color(progress_bar(index, total_cases), Color.YELLOW))
        print(color(f"[{index}/{total_cases}] {case.name}", Color.BLUE + Color.BOLD))
        print(f"Script: {case.script}")
        print(f"Description: {case.description}")

        if script_status(case) != "found":
            result = {
                "name": case.name,
                "script": case.script,
                "command": [],
                "command_display": "",
                "return_code": -2,
                "duration_seconds": 0,
                "success": False,
                "stdout": "",
                "stderr": "Script file is missing",
            }
        else:
            command = build_command(case, course_id, quick=quick)
            print(f"Command: {format_command(command)}")
            result = run_case(case, course_id, quick=quick, base_url=args.base_url)
            print(f"Result: {status_label(result['success'])} in {result['duration_seconds']:.2f}s")
        results.append(result)

    result_path = save_results(results, base_url=args.base_url, quick=quick)
    passed = sum(1 for result in results if result["success"])
    failed = len(results) - passed

    print_section("Stress test summary")
    for result in results:
        print(
            f"{status_label(result['success'])}  "
            f"{result['name']:<24} "
            f"{result['duration_seconds']:>7.2f}s"
        )

    print()
    print(f"Results saved to: {result_path}")

    summary_text = f"Summary: {passed} passed, {failed} failed"
    if failed == 0:
        print(color(summary_text, Color.GREEN + Color.BOLD))
    else:
        print(color(summary_text, Color.RED + Color.BOLD))

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
