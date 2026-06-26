"""
Find observed local stress limits for safe backend stress tests.

This script is intended for local testing only. It runs selected stress tests
with gradually increasing load levels and reports the highest stable passing
load observed in the current local environment.

Usage:
    python backend/test/stress/find_local_stress_limit.py COURSE_ID

Examples:
    python backend/test/stress/find_local_stress_limit.py COURSE_ID
    python backend/test/stress/find_local_stress_limit.py COURSE_ID --only bulk_uploads --loads 10,25,50,75,100
    python backend/test/stress/find_local_stress_limit.py COURSE_ID --only assignment_creation --loads 5,10,25,50 --repeat 3
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "results"


class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def color(text: str, code: str) -> str:
    if os.environ.get("NO_COLOR"):
        return text
    return f"{code}{text}{Color.RESET}"


def print_section(title: str) -> None:
    line = "=" * 72
    print()
    print(color(line, Color.CYAN))
    print(color(title, Color.CYAN + Color.BOLD))
    print(color(line, Color.CYAN))


def output_has_failure(output: str) -> bool:
    failure_markers = (
        "Test failed:",
        "Failed to run stress test:",
        "Error uploading submission:",
        "] Error:",
        "Thread failed with exception:",
        "Task failed with exception:",
        "Traceback",
        "UnicodeEncodeError",
        "ConnectionError",
        "Connection refused",
        "Read timed out",
        "500 Server Error",
        "400 Client Error",
    )
    return any(marker in output for marker in failure_markers)


def run_command(command: list[str], timeout_seconds: int = 900) -> dict:
    start = time.time()

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    try:
        result = subprocess.run(
            command,
            cwd=SCRIPT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            env=env,
        )

        duration = time.time() - start
        combined_output = f"{result.stdout}\n{result.stderr}"
        success = result.returncode == 0 and not output_has_failure(combined_output)

        return {
            "command": command,
            "command_display": " ".join(command),
            "success": success,
            "return_code": result.returncode,
            "duration_seconds": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.TimeoutExpired as error:
        return {
            "command": command,
            "command_display": " ".join(command),
            "success": False,
            "return_code": -1,
            "duration_seconds": time.time() - start,
            "stdout": error.stdout or "",
            "stderr": f"Timed out after {timeout_seconds} seconds",
        }


def build_bulk_upload_command(course_id: str, load: int) -> list[str]:
    workers = max(1, min(20, load // 5))

    return [
        sys.executable,
        str(SCRIPT_DIR / "test_bulk_assignment_uploads.py"),
        course_id,
        "--num_uploads",
        str(load),
        "--max_workers",
        str(workers),
        "--cleanup",
    ]


def build_student_submission_command(course_id: str, load: int) -> list[str]:
    return [
        sys.executable,
        str(SCRIPT_DIR / "upload_assignments.py"),
        course_id,
        "--num_threads",
        str(load),
        "--cleanup",
    ]


def build_assignment_creation_command(course_id: str, load: int) -> list[str]:
    return [
        sys.executable,
        str(SCRIPT_DIR / "create_assignments.py"),
        str(load),
        course_id,
    ]


STRESS_CASES = {
    "bulk_uploads": {
        "description": "Assignment/autograder uploads",
        "builder": build_bulk_upload_command,
    },
    "student_submissions": {
        "description": "Concurrent student submissions",
        "builder": build_student_submission_command,
    },
    "assignment_creation": {
        "description": "Concurrent assignment creation",
        "builder": build_assignment_creation_command,
    },
}


def summarize_load_runs(runs: list[dict], repeat: int) -> dict:
    passed_runs = [run for run in runs if run["success"]]
    failed_runs = [run for run in runs if not run["success"]]
    durations = [run["duration_seconds"] for run in runs]

    pass_count = len(passed_runs)
    fail_count = len(failed_runs)
    pass_rate = pass_count / repeat if repeat else 0

    if pass_count == repeat:
        status = "stable_pass"
    elif pass_count == 0:
        status = "failed"
    else:
        status = "unstable"

    return {
        "status": status,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "repeat": repeat,
        "pass_rate": pass_rate,
        "avg_duration_seconds": sum(durations) / len(durations) if durations else None,
        "min_duration_seconds": min(durations) if durations else None,
        "max_duration_seconds": max(durations) if durations else None,
    }


def print_failure_details(result: dict) -> None:
    print(f"Return code: {result['return_code']}")

    if result["stderr"]:
        print()
        print("STDERR:")
        print(result["stderr"][-2000:])

    if result["stdout"]:
        print()
        print("STDOUT tail:")
        print(result["stdout"][-3000:])


def run_limit_search(
    course_id: str,
    loads: list[int],
    only: list[str] | None,
    repeat: int,
    continue_after_failure: bool,
) -> list[dict]:
    selected_cases = only or list(STRESS_CASES.keys())
    all_results = []

    print_section("Observed Local Stress Limit Search")
    print(f"Course ID: {course_id}")
    print(f"Load levels: {loads}")
    print(f"Repeat per load: {repeat}")
    print(f"Continue after failure: {continue_after_failure}")
    print(f"Cases: {selected_cases}")

    for case_name in selected_cases:
        case_config = STRESS_CASES[case_name]
        load_results = []
        highest_stable_passed = None
        first_unstable_or_failed = None

        print_section(f"Testing {case_name}")
        print(case_config["description"])

        for load in loads:
            command = case_config["builder"](course_id, load)
            runs_for_load = []

            print()
            print(color(f"Running {case_name} at load {load}", Color.YELLOW + Color.BOLD))
            print("Command:")
            print(" ".join(command))

            for attempt in range(1, repeat + 1):
                print()
                print(f"Attempt {attempt}/{repeat}")

                result = run_command(command)
                result["case"] = case_name
                result["load"] = load
                result["attempt"] = attempt

                runs_for_load.append(result)

                if result["success"]:
                    print(color(f"PASS in {result['duration_seconds']:.2f}s", Color.GREEN + Color.BOLD))
                else:
                    print(color(f"FAIL in {result['duration_seconds']:.2f}s", Color.RED + Color.BOLD))
                    print_failure_details(result)

            load_summary = summarize_load_runs(runs_for_load, repeat)

            load_result = {
                "load": load,
                "summary": load_summary,
                "runs": runs_for_load,
            }
            load_results.append(load_result)

            status = load_summary["status"]
            pass_count = load_summary["pass_count"]
            avg_duration = load_summary["avg_duration_seconds"]
            max_duration = load_summary["max_duration_seconds"]

            if status == "stable_pass":
                highest_stable_passed = load
                print(
                    color(
                        f"LOAD {load}: STABLE PASS "
                        f"({pass_count}/{repeat} passed, "
                        f"avg {avg_duration:.2f}s, max {max_duration:.2f}s)",
                        Color.GREEN + Color.BOLD,
                    )
                )
            else:
                if first_unstable_or_failed is None:
                    first_unstable_or_failed = load

                label = "UNSTABLE" if status == "unstable" else "FAILED"
                print(
                    color(
                        f"LOAD {load}: {label} "
                        f"({pass_count}/{repeat} passed, "
                        f"avg {avg_duration:.2f}s, max {max_duration:.2f}s)",
                        Color.RED + Color.BOLD,
                    )
                )

                if not continue_after_failure:
                    print("Stopping this case after first unstable or failed load.")
                    break

        all_results.append(
            {
                "case": case_name,
                "description": case_config["description"],
                "highest_stable_passed": highest_stable_passed,
                "first_unstable_or_failed": first_unstable_or_failed,
                "loads": load_results,
            }
        )

    return all_results


def save_results(
    results: list[dict],
    course_id: str,
    loads: list[int],
    repeat: int,
    continue_after_failure: bool,
) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_path = RESULTS_DIR / f"local_stress_limit_results_{timestamp}.json"

    payload = {
        "created_at": datetime.now().isoformat(),
        "course_id": course_id,
        "load_levels": loads,
        "repeat": repeat,
        "continue_after_failure": continue_after_failure,
        "results": results,
    }

    result_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return result_path


def print_summary(results: list[dict]) -> None:
    print_section("Observed Local Stable Max Summary")

    for result in results:
        case_name = result["case"]
        highest_stable_passed = result["highest_stable_passed"]
        first_unstable_or_failed = result["first_unstable_or_failed"]

        if highest_stable_passed is None:
            print(color(f"{case_name}: no stable passing load observed", Color.RED + Color.BOLD))
        elif first_unstable_or_failed is None:
            print(
                color(
                    f"{case_name}: max tested load {highest_stable_passed} was stable; no failure observed",
                    Color.GREEN + Color.BOLD,
                )
            )
        else:
            print(
                color(
                    f"{case_name}: highest stable passed {highest_stable_passed}; "
                    f"first unstable/failed {first_unstable_or_failed}",
                    Color.YELLOW + Color.BOLD,
                )
            )

    print()
    print("Note: These are observed local results, not guaranteed system-wide limits.")
    print("A load is treated as stable only if all repeated attempts pass.")


def parse_loads(load_string: str) -> list[int]:
    loads = []

    for value in load_string.split(","):
        value = value.strip()
        if value:
            loads.append(int(value))

    return loads


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find observed local stress limits.")
    parser.add_argument("course_id", help="Real course ID")
    parser.add_argument(
        "--loads",
        default="10,25,50,75,100",
        help="Comma-separated load levels. Default: 10,25,50,75,100",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of times to repeat each load level. Default: 1",
    )
    parser.add_argument(
        "--continue-after-failure",
        action="store_true",
        help="Continue testing higher loads after an unstable or failed load.",
    )
    parser.add_argument(
        "--only",
        action="append",
        choices=list(STRESS_CASES.keys()),
        help="Run only one case. Can be repeated.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.repeat < 1:
        raise ValueError("--repeat must be at least 1")

    loads = parse_loads(args.loads)

    results = run_limit_search(
        course_id=args.course_id,
        loads=loads,
        only=args.only,
        repeat=args.repeat,
        continue_after_failure=args.continue_after_failure,
    )

    result_path = save_results(
        results=results,
        course_id=args.course_id,
        loads=loads,
        repeat=args.repeat,
        continue_after_failure=args.continue_after_failure,
    )

    print_summary(results)

    print()
    print(f"Results saved to: {result_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())