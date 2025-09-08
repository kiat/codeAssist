# Stress Test Suite

This directory contains comprehensive stress tests to evaluate the backend system's performance under various load conditions. These tests help identify bottlenecks, race conditions, and scalability issues before deployment.

## Available Tests

### 1. Bulk Assignment Uploads (`test_bulk_assignment_uploads.py`)
**Purpose**: Test backend handling of multiple assignment uploads concurrently.

**What it tests**:
- Upload 20+ zip files concurrently via `/upload_assignment`
- Measures upload success rate, request times
- Monitors server CPU/memory usage (optional)
- Provides detailed performance metrics

**Usage**:
```bash
python test_bulk_assignment_uploads.py <course_id> [options]

Options:
  --num_uploads N          Number of uploads (default: 20)
  --max_workers N          Concurrent workers (default: 8)
  --zip_size_mb N         Test file size in MB (default: 2)
  --monitor_system        Enable system resource monitoring
  --cleanup              Delete created assignments after test
```

**Example**:
```bash
python test_bulk_assignment_uploads.py 123e4567-e89b-12d3-a456-426614174000 --num_uploads 25 --monitor_system --cleanup
```

### 2. Long-Running Grader Test (`test_long_running_grader.py`)
**Purpose**: Test if the grader can handle long code execution without failing.

**What it tests**:
- Submissions with various execution times (1s, 5s, 10s, 20s)
- CPU-intensive tasks (Fibonacci calculations)
- Grading timeout handling
- State consistency during long operations

**Usage**:
```bash
python test_long_running_grader.py <course_id> [options]

Options:
  --max_execution_time N   Maximum test execution time (default: 20)
  --num_submissions N      Submissions per test type (default: 1)
  --max_workers N          Concurrent workers (default: 5)
  --cleanup               Delete created resources
```

### 3. Concurrent Enrollment Test (`test_concurrent_enrollment.py`)
**Purpose**: Test rapid enrollment/unenrollment of users in parallel threads.

**What it tests**:
- Multiple threads enrolling/unenrolling same user simultaneously
- Race condition detection
- Database locking and consistency
- State verification after operations

**Usage**:
```bash
python test_concurrent_enrollment.py <course_id> [options]

Options:
  --num_threads N              Concurrent threads (default: 5)
  --operations_per_thread N    Operations per thread (default: 10)
  --max_workers N              Max concurrent workers (default: 10)
  --cleanup                   Delete created users
```

### 4. Concurrent CRUD Operations (`test_concurrent_crud_operations.py`)
**Purpose**: Test creating/deleting courses and assignments while other threads query/modify them.

**What it tests**:
- Concurrent course creation, deletion, and queries
- Concurrent assignment operations
- Race conditions during resource lifecycle
- Database consistency under load

**Usage**:
```bash
python test_concurrent_crud_operations.py [options]

Options:
  --num_threads N              Concurrent threads (default: 6)
  --operations_per_thread N    Operations per thread (default: 15)
  --test_type TYPE            'courses', 'assignments', 'mixed', or 'both'
  --cleanup                   Delete created resources
```

**Test Types**:
- `courses`: Focus on course CRUD operations
- `assignments`: Focus on assignment CRUD operations  
- `mixed`: Each thread does both course and assignment operations
- `both`: Half threads do courses, half do assignments

### 5. Student Submission Test (`upload_assignments.py`)
**Purpose**: Simulate multiple students submitting code to the same assignment concurrently.

**Usage**:
```bash
python upload_assignments.py <course_id> [options]

Options:
  --num_threads N    Concurrent student submissions (default: 5)
  --cleanup         Delete created assignment and students
```

### 6. Assignment Creation Test (`create_assignments.py`) 
**Purpose**: Test concurrent assignment creation with autograder uploads.

**Usage**:
```bash
python create_assignments.py <num_threads> <course_id>
```

## Comprehensive Test Runner

The `run_all_stress_tests.py` script executes all stress tests in sequence and provides consolidated reporting.

**Usage**:
```bash
python run_all_stress_tests.py <course_id> [options]

Options:
  --quick        Run with reduced load for faster execution
  --cleanup      Clean up resources after each test (default: True)
  --no-cleanup   Don't clean up created resources
```

**Quick Mode**: Reduces test parameters for faster execution during development.
**Full Mode**: Uses production-like load parameters to thoroughly test system limits.

## Prerequisites

### 1. Backend Server
Ensure the Flask backend server is running on `http://localhost:5001` before executing any stress tests.

### 2. Dependencies
Install required Python packages:
```bash
pip install requests psutil
```

### 3. Test Data
Some tests require the autograder example:
- Ensure `../../assignment-examples/A1/A1.zip` exists, or
- Use `--use_custom_zip` option to specify a different zip file

### 4. Valid Course ID
All tests require a valid course ID. You can create one using the backend API:
```bash
curl -X POST http://localhost:5001/create_course \
  -H "Content-Type: application/json" \
  -d '{"name": "Stress Test Course", "instructor_id": "your-instructor-id"}'
```

## Running Individual Tests

### Quick Start Examples

1. **Test bulk uploads with monitoring**:
```bash
python test_bulk_assignment_uploads.py abc123-course-id --num_uploads 20 --monitor_system --cleanup
```

2. **Test long-running grading**:
```bash
python test_long_running_grader.py abc123-course-id --max_execution_time 15 --num_submissions 2
```

3. **Test concurrent enrollment**:
```bash
python test_concurrent_enrollment.py abc123-course-id --num_threads 8 --operations_per_thread 10
```

4. **Test CRUD operations**:
```bash
python test_concurrent_crud_operations.py --test_type mixed --num_threads 6
```

### Run All Tests
```bash
# Full comprehensive test suite
python run_all_stress_tests.py abc123-course-id --cleanup

# Quick development testing
python run_all_stress_tests.py abc123-course-id --quick --cleanup
```

## Understanding Test Results

### Success Metrics
- **Success Rate**: Percentage of operations that completed successfully
- **Response Times**: Average, median, min, max operation durations
- **Throughput**: Operations per second, data transfer rates
- **Resource Usage**: CPU, memory, disk, and network utilization

### Warning Signs
- Success rate < 95%: Potential server overload or bugs
- High response time variance: Possible database locking issues
- Memory usage spikes: Memory leaks or inefficient resource handling
- Thread failures distributed across many workers: System-wide bottlenecks

### Common Issues and Solutions

| Issue | Symptoms | Potential Solutions |
|-------|----------|-------------------|
| Database locks | High failure rate, timeouts | Optimize queries, add connection pooling |
| Memory leaks | Steadily increasing memory usage | Profile application, fix resource cleanup |
| CPU bottlenecks | High CPU usage, slow responses | Optimize algorithms, add caching |
| File I/O issues | Slow upload times | Use async I/O, optimize file handling |
| Race conditions | Inconsistent state, intermittent failures | Add proper locking, review concurrent code |

## Test Output Analysis

### Standard Output
Each test provides real-time progress updates and a comprehensive summary including:
- Operation counts and success rates
- Performance metrics (timing, throughput)
- Resource usage statistics
- Error analysis and categorization
- Thread-level performance breakdown

### Generated Files
- `stress_test_results_YYYYMMDD_HHMMSS.json`: Detailed results in JSON format
- `generated_assignments.json`: Assignment IDs created during tests (for cleanup)

### Sample Output Interpretation
```
BULK ASSIGNMENT UPLOAD STRESS TEST RESULTS
==========================================
OVERALL PERFORMANCE:
  Total uploads attempted: 25
  Successful uploads: 24 (96.0%)
  Failed uploads: 1 (4.0%)
  Test duration: 45.23s

TIMING STATISTICS:
  Average upload time: 1.85s
  Median upload time: 1.72s
  Min upload time: 0.95s
  Max upload time: 4.23s

THROUGHPUT:
  Successful uploads per second: 0.53
  Data throughput: 1.06 MB/s
```

**Interpretation**: This shows good performance with 96% success rate and consistent timing.

## Integration with CI/CD

### Automated Testing
Add stress tests to your CI pipeline:
```yaml
# Example GitHub Actions workflow
- name: Run Stress Tests
  run: |
    python test/stress/run_all_stress_tests.py ${{ secrets.TEST_COURSE_ID }} --quick --cleanup
  timeout-minutes: 30
```

### Specific Testing 
Run an individual test with:
# Test bulk uploads with monitoring
python test_bulk_assignment_uploads.py your-course-id --num_uploads 25 --monitor_system --cleanup

# Test long-running operations
python test_long_running_grader.py your-course-id --max_execution_time 20 --num_submissions 3
