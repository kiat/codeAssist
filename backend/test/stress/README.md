# Local Stress Test Guide

This folder contains backend stress-test scripts. For local thesis/testing work,
start with the safer wrapper:

```bash
python backend/test/stress/run_local_stress_tests.py --dry-run
```

The old examples use `<course_id>` as a placeholder. Do not type the angle
brackets in Git Bash. Bash treats `<course_id>` as file input redirection.

Use a real course id:

```bash
COURSE_ID=replace-with-real-course-id
python backend/test/stress/run_local_stress_tests.py "$COURSE_ID" --run-safe
```

## Recommended Workflow

Run these commands from the repository root:

```bash
python -m compileall backend/test/stress
python backend/test/stress/run_local_stress_tests.py --check-server
```

If the preflight looks good and the backend is running on `http://localhost:5001`,
run the safe smoke tests:

```bash
COURSE_ID=replace-with-real-course-id
python backend/test/stress/run_local_stress_tests.py "$COURSE_ID" --run-safe
```

Results are written to:

```text
backend/test/stress/results/
```

## Getting A Course ID

You can use a course id from the UI, from the local database, or from a course
created through the API. The current backend requires `name`, `instructor_id`,
`semester`, `year`, and `entryCode` for `/create_course`.

Example API setup:

```bash
curl -X POST http://localhost:5001/create_user \
  -H "Content-Type: application/json" \
  -d '{"name":"Stress Instructor","email_address":"stress-instructor@example.com","password":"test123","eid":"stressinst001","role":"Instructor"}'
```

Copy the returned `id`, then create a course:

```bash
curl -X POST http://localhost:5001/create_course \
  -H "Content-Type: application/json" \
  -d '{"name":"Stress Test Course","instructor_id":"PASTE_INSTRUCTOR_ID","semester":"Fall","year":"2026","entryCode":"STRESS2026"}'
```

Copy the returned course `id`.

## Test Status

Safe through `run_local_stress_tests.py`:

- `bulk_uploads`
- `student_submissions`
- `assignment_creation`

Manual:

- `long_running_grader`: slow and currently waits with `sleep` instead of
  polling real grading status.

Known incompatible with this backend until updated:

- `concurrent_enrollment`: calls `/enroll_user`, `/unenroll_user`, and
  `/get_user_courses`, but this backend exposes `/create_enrollment`,
  `/leave_course`, and `/get_user_enrollments`.
- `crud_operations`: creates courses without `semester`, `year`, and
  `entryCode`, and calls `/get_course` instead of `/get_course_info`.

## Running Individual Old Scripts

If you run an original script directly, first enter this folder because several
scripts use relative fixture paths:

```bash
cd backend/test/stress
COURSE_ID=replace-with-real-course-id
python test_bulk_assignment_uploads.py "$COURSE_ID" --num_uploads 2 --max_workers 1 --cleanup
python upload_assignments.py "$COURSE_ID" --num_threads 2 --cleanup
python create_assignments.py 2 "$COURSE_ID"
```

Prefer the local wrapper for repeatable reports.
