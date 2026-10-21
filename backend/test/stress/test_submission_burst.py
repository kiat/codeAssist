"""
Stress test: N students submit to one assignment at the same time.

Usage:
    python test_submission_burst.py <course_id> --students 20 --instructor-email <email> --instructor-password <password>
"""

import argparse
import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime

import requests

from utils import BASE_URL, raise_for_status_with_body

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXAMPLES_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "assignment-examples", "A1"))
DEFAULT_AUTOGRADER = os.path.join(EXAMPLES_DIR, "A1.zip")
DEFAULT_SUBMISSION = os.path.join(EXAMPLES_DIR, "calculator.py")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
STUDENT_PASSWORD = "burst-pass-123"


def login(email, password):
    http = requests.Session()
    response = http.post(f"{BASE_URL}/user_login", json={"email": email, "password": password})
    raise_for_status_with_body(response, f"Log in as {email}")
    return http, response.json()["id"]


def student_session(index):
    email = f"burst-student-{index:04d}@stress.test"
    http = requests.Session()
    response = http.post(
        f"{BASE_URL}/create_user",
        json={
            "name": f"Burst Student {index}",
            "email_address": email,
            "password": STUDENT_PASSWORD,
            "eid": f"burst{index:04d}",
            "role": "Student",
        },
    )
    if response.status_code == 409:
        return login(email, STUDENT_PASSWORD)
    raise_for_status_with_body(response, f"Create {email}")
    return http, response.json()["id"]


def prepare_assignment(instructor, course_id, autograder_path, timeout):
    response = instructor.post(
        f"{BASE_URL}/create_assignment",
        json={
            "name": f"burst-{uuid.uuid4().hex[:8]}",
            "course_id": course_id,
            "published": True,
            "allow_file_upload": True,
        },
    )
    raise_for_status_with_body(response, "Create assignment")
    assignment_id = response.json()["id"]

    with open(autograder_path, "rb") as file:
        response = instructor.post(
            f"{BASE_URL}/upload_assignment_autograder",
            files={"file": (os.path.basename(autograder_path), file, "application/zip")},
            data={"assignment_id": assignment_id, "autograder_timeout": str(timeout)},
            timeout=900,
        )
    raise_for_status_with_body(response, "Upload autograder")
    return assignment_id


def submit(http, student_id, assignment_id, submission_bytes, filename, request_timeout):
    started = time.perf_counter()
    result = {"student_id": student_id, "start": started}
    try:
        response = http.post(
            f"{BASE_URL}/upload_submission",
            files={"file": (filename, submission_bytes, "text/x-python")},
            data={"assignment_id": assignment_id, "student_id": student_id},
            timeout=request_timeout,
        )
        result["status"] = response.status_code
        if response.status_code != 200:
            result["error"] = response.text[:300]
    except requests.RequestException as error:
        result["status"] = "client_error"
        result["error"] = f"{type(error).__name__}: {error}"[:300]
    result["end"] = time.perf_counter()
    result["latency"] = result["end"] - started
    return result


def run_burst(sessions, assignment_id, submission_path, request_timeout):
    with open(submission_path, "rb") as file:
        submission_bytes = file.read()
    filename = os.path.basename(submission_path)

    barrier = threading.Barrier(len(sessions))
    results = [None] * len(sessions)

    def worker(index, http, student_id):
        barrier.wait()
        results[index] = submit(http, student_id, assignment_id, submission_bytes, filename, request_timeout)

    threads = [
        threading.Thread(target=worker, args=(index, http, student_id))
        for index, (http, student_id) in enumerate(sessions)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    position = min(len(ordered) - 1, max(0, round(fraction * (len(ordered) - 1))))
    return ordered[position]


def summarize(results):
    ok = [r for r in results if r["status"] == 200]
    latencies = [r["latency"] for r in ok]
    wall = max(r["end"] for r in results) - min(r["start"] for r in results)

    statuses = {}
    for r in results:
        statuses[str(r["status"])] = statuses.get(str(r["status"]), 0) + 1

    return {
        "submissions": len(results),
        "succeeded": len(ok),
        "statuses": statuses,
        "wall_seconds": round(wall, 3),
        "throughput_per_second": round(len(ok) / wall, 3) if wall else None,
        "latency_seconds": {
            "min": round(min(latencies), 3) if latencies else None,
            "p50": round(percentile(latencies, 0.5), 3) if latencies else None,
            "p95": round(percentile(latencies, 0.95), 3) if latencies else None,
            "max": round(max(latencies), 3) if latencies else None,
        },
        "sample_errors": [r["error"] for r in results if r.get("error")][:5],
    }


def print_summary(summary):
    latency = summary["latency_seconds"]
    print()
    print(f"Submissions: {summary['submissions']}  succeeded: {summary['succeeded']}  statuses: {summary['statuses']}")
    print(f"Wall time: {summary['wall_seconds']}s  throughput: {summary['throughput_per_second']} submissions/s")
    print(f"Latency (successes): min {latency['min']}s  p50 {latency['p50']}s  p95 {latency['p95']}s  max {latency['max']}s")
    for error in summary["sample_errors"]:
        print(f"  error: {error}")


def main():
    parser = argparse.ArgumentParser(description="Burst of simultaneous submissions to one assignment.")
    parser.add_argument("course_id", help="Course the instructor teaches")
    parser.add_argument("--students", type=int, default=20, help="Number of simultaneous submissions")
    parser.add_argument("--instructor-email", default=os.environ.get("STRESS_INSTRUCTOR_EMAIL"))
    parser.add_argument("--instructor-password", default=os.environ.get("STRESS_INSTRUCTOR_PASSWORD"))
    parser.add_argument("--assignment-id", help="Reuse an existing assignment instead of creating one")
    parser.add_argument("--autograder", default=DEFAULT_AUTOGRADER)
    parser.add_argument("--submission", default=DEFAULT_SUBMISSION)
    parser.add_argument("--autograder-timeout", type=int, default=30)
    parser.add_argument("--request-timeout", type=float, default=600, help="Client-side timeout per submission, seconds")
    parser.add_argument("--no-warmup", action="store_true", help="Skip the single submission sent before the burst")
    parser.add_argument("--cleanup", action="store_true", help="Delete the created assignment afterwards")
    args = parser.parse_args()

    if args.students < 1:
        print("--students must be at least 1")
        return 1
    if not (args.instructor_email and args.instructor_password):
        print("Need --instructor-email and --instructor-password")
        return 1

    instructor = None
    created_assignment = False
    try:
        instructor, _ = login(args.instructor_email, args.instructor_password)

        assignment_id = args.assignment_id
        if not assignment_id:
            print("Creating assignment and building the autograder image...")
            assignment_id = prepare_assignment(instructor, args.course_id, args.autograder, args.autograder_timeout)
            created_assignment = True
        print(f"Assignment: {assignment_id}")

        print(f"Preparing {args.students} student sessions...")
        sessions = [student_session(index) for index in range(args.students)]
        for _, student_id in sessions:
            response = instructor.post(
                f"{BASE_URL}/create_enrollment",
                json={"student_id": student_id, "course_id": args.course_id},
            )
            if response.status_code not in (201, 409):
                raise_for_status_with_body(response, "Enroll student")

        if not args.no_warmup:
            warmup = run_burst(sessions[:1], assignment_id, args.submission, args.request_timeout)[0]
            print(f"Warm-up submission: status {warmup['status']}, {warmup['latency']:.3f}s")

        print(f"Releasing {args.students} submissions at once...")
        results = run_burst(sessions, assignment_id, args.submission, args.request_timeout)
        summary = summarize(results)
        print_summary(summary)

        os.makedirs(RESULTS_DIR, exist_ok=True)
        output_path = os.path.join(RESULTS_DIR, f"submission_burst_{args.students}_{datetime.now():%Y%m%d_%H%M%S_%f}.json")
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump({"base_url": BASE_URL, "assignment_id": assignment_id, "summary": summary, "results": results}, file, indent=2)
        print(f"\nSaved {output_path}")

        return 0 if summary["succeeded"] == summary["submissions"] else 1
    finally:
        if args.cleanup and created_assignment and instructor is not None:
            response = instructor.delete(f"{BASE_URL}/delete_assignment", params={"assignment_id": assignment_id})
            print(f"Cleanup: delete assignment -> {response.status_code}")


if __name__ == "__main__":
    sys.exit(main())
