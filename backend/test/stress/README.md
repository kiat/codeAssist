# Backend Stress Tests

This folder contains manual backend stress tests for local performance checks.
They are not pytest tests and are not meant to run inside `make test`.

## Fast Path

Start the backend first, then run these commands from the repository root.

```bash
python -m compileall backend/test/stress
python backend/test/stress/run_local_stress_tests.py --check-server
```

Use a real course id. Do not type `<course_id>` in Git Bash because `<...>` is
shell input redirection.

Git Bash:

```bash
# COURSE_ID=f57ac0e3-7ff6-4eca-b1af-37f360de2cd7
COURSE_ID=replace-with-real-course-id
python backend/test/stress/run_local_stress_tests.py "$COURSE_ID" --run-safe
```

PowerShell:

```powershell
$env:COURSE_ID = "replace-with-real-course-id"
python backend/test/stress/run_local_stress_tests.py $env:COURSE_ID --run-safe
```

The quick safe suite runs all six stress areas with conservative local load:

- bulk assignment uploads
- student submissions
- assignment creation
- long-running grader submissions
- concurrent enrollment and leave-course operations
- concurrent course and assignment CRUD operations

Results are saved under `backend/test/stress/results/`.

## Runner Choices

Use `run_local_stress_tests.py` while developing or debugging. It has preflight
checks, command preview, stable result files, and the safest defaults.

```bash
# COURSE_ID=f57ac0e3-7ff6-4eca-b1af-37f360de2cd7
python backend/test/stress/run_local_stress_tests.py --dry-run
python backend/test/stress/run_local_stress_tests.py "$COURSE_ID" --run-safe
python backend/test/stress/run_local_stress_tests.py "$COURSE_ID" --run-safe --full
python backend/test/stress/run_local_stress_tests.py "$COURSE_ID" --run-safe --only crud_operations
```

Use `run_all_stress_tests.py` when you want the legacy PR-style report.

```bash
python backend/test/stress/run_all_stress_tests.py "$COURSE_ID" --quick --cleanup
python backend/test/stress/run_all_stress_tests.py "$COURSE_ID" --cleanup
```

## Reading Results

Each script exits with code `0` only when its own stress checks passed. The
summary separates:

- `PASS`: request completed successfully.
- `CONFLICT`: expected concurrent race, such as duplicate enrollment or querying
  something another worker already deleted.
- `SKIP`: no active resource was available for that operation.
- `FAIL`: unexpected backend error, request error, or script setup failure.

If the backend logs show `QueuePool limit ... connection timed out`, the test
found a database connection-pool capacity limit. For a thesis/performance
report, record the load level, worker count, and endpoint. For local debugging,
reduce `--max_workers` first, then inspect backend session cleanup and SQLAlchemy
pool settings.

## Manual Scripts

For individual scripts, run from this folder so fixture paths resolve correctly:

```bash
cd backend/test/stress
python test_bulk_assignment_uploads.py "$COURSE_ID" --num_uploads 2 --max_workers 1 --cleanup
python upload_assignments.py "$COURSE_ID" --num_threads 2 --cleanup
python create_assignments.py 2 "$COURSE_ID" --cleanup
python test_long_running_grader.py "$COURSE_ID" --max_execution_time 1 --num_submissions 1 --max_workers 1 --cleanup
python test_concurrent_enrollment.py "$COURSE_ID" --num_threads 1 --operations_per_thread 2 --max_workers 1 --cleanup
python test_concurrent_crud_operations.py --num_threads 1 --operations_per_thread 2 --test_type mixed --max_workers 1 --cleanup
```

Use `--no-cleanup` only when you intentionally want to inspect created resources
in the app or database afterward.


Short version:

```bash
python -m compileall backend/test/stress
python backend/test/stress/run_local_stress_tests.py --check-server
COURSE_ID=replace-with-real-course-id
python backend/test/stress/run_local_stress_tests.py "$COURSE_ID" --run-safe
```

Do not type `<course_id>` literally in Git Bash.
