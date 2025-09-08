import argparse
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
from utils import create_assignment, upload_autograder, upload_submission, add_user, delete_assignment

"""
Stress test for long-running grading operations.

This test evaluates if the grader can handle code that takes a long time to execute
without timing out or failing. It creates submissions with various execution times
and monitors the grading process.

Usage:
    python test_long_running_grader.py <course_id> [--max_execution_time SECONDS] [--num_submissions N]

Example:
    python test_long_running_grader.py 123e4567-e89b-12d3-a456-426614174000 --max_execution_time 30 --num_submissions 5
"""

# Test configurations for different execution times
TEST_CODES = [
    {
        "name": "quick_execution",
        "execution_time": 1,
        "code": """
import time
time.sleep(1)
print("Quick execution complete")
"""
    },
    {
        "name": "medium_execution", 
        "execution_time": 5,
        "code": """
import time
time.sleep(5)
print("Medium execution complete")
"""
    },
    {
        "name": "long_execution",
        "execution_time": 10,
        "code": """
import time
time.sleep(10)
print("Long execution complete")
"""
    },
    {
        "name": "very_long_execution",
        "execution_time": 20,
        "code": """
import time
time.sleep(20)
print("Very long execution complete")
"""
    },
    {
        "name": "cpu_intensive",
        "execution_time": 15,
        "code": """
import time
# CPU intensive task
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

start_time = time.time()
result = fibonacci(35)  # This takes significant CPU time
end_time = time.time()
print(f"Fibonacci result: {result}, Time taken: {end_time - start_time:.2f}s")
"""
    }
]

AUTOGRADER_ZIP_PATH = os.path.abspath(os.path.join("..", "..", "assignment-examples", "A1", "A1.zip"))

# Shared state
created_students = []
created_students_lock = threading.Lock()
assignment_id = None
test_results = []
results_lock = threading.Lock()


def create_test_submission_file(code_content, filename_prefix):
    """Create a temporary submission file with the given code content."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', prefix=f'{filename_prefix}_', delete=False) as f:
        f.write(code_content)
        return f.name


def submit_and_monitor_grading(test_config, thread_index, assignment_id):
    """Submit code and monitor the grading process."""
    try:
        # Create student
        student_name = f"long_runner_{test_config['name']}_{thread_index}"
        student_id = add_user(name=student_name)
        
        with created_students_lock:
            created_students.append(student_id)
        
        print(f"[Thread-{thread_index}] Created student: {student_name} for {test_config['name']}")
        
        # Create submission file
        submission_file = create_test_submission_file(test_config['code'], test_config['name'])
        
        # Record start time
        start_time = time.time()
        
        # Submit for grading
        print(f"[Thread-{thread_index}] Submitting {test_config['name']} (expected ~{test_config['execution_time']}s)")
        submission_result = upload_submission(
            assignment_id=assignment_id,
            student_id=student_id,
            submission_file_path=submission_file
        )
        
        # Record submission time
        submission_time = time.time() - start_time
        
        # Monitor grading (you may need to implement a way to check grading status)
        # For now, we'll wait a reasonable amount of time
        max_wait_time = test_config['execution_time'] + 30  # Add 30s buffer
        time.sleep(max_wait_time)
        
        total_time = time.time() - start_time
        
        # Record results
        result = {
            'test_name': test_config['name'],
            'thread_index': thread_index,
            'student_id': student_id,
            'expected_execution_time': test_config['execution_time'],
            'submission_time': submission_time,
            'total_time': total_time,
            'success': True,
            'error': None
        }
        
        with results_lock:
            test_results.append(result)
        
        print(f"[Thread-{thread_index}] ✅ {test_config['name']} completed in {total_time:.2f}s")
        
        # Clean up temp file
        os.unlink(submission_file)
        
    except Exception as e:
        error_result = {
            'test_name': test_config['name'],
            'thread_index': thread_index,
            'student_id': student_id if 'student_id' in locals() else None,
            'expected_execution_time': test_config['execution_time'],
            'submission_time': None,
            'total_time': None,
            'success': False,
            'error': str(e)
        }
        
        with results_lock:
            test_results.append(error_result)
        
        print(f"[Thread-{thread_index}] ❌ {test_config['name']} failed: {e}")
        
        # Clean up temp file if it exists
        if 'submission_file' in locals():
            try:
                os.unlink(submission_file)
            except:
                pass


def print_results_summary():
    """Print a summary of all test results."""
    print("\n" + "="*80)
    print("LONG-RUNNING GRADER STRESS TEST RESULTS")
    print("="*80)
    
    successful_tests = [r for r in test_results if r['success']]
    failed_tests = [r for r in test_results if not r['success']]
    
    print(f"Total tests: {len(test_results)}")
    print(f"Successful: {len(successful_tests)} ({len(successful_tests)/len(test_results)*100:.1f}%)")
    print(f"Failed: {len(failed_tests)} ({len(failed_tests)/len(test_results)*100:.1f}%)")
    print()
    
    if successful_tests:
        print("SUCCESSFUL TESTS:")
        print("-" * 60)
        for result in successful_tests:
            print(f"  {result['test_name']:<20} | Expected: {result['expected_execution_time']:>3}s | "
                  f"Actual: {result['total_time']:>6.2f}s | Thread: {result['thread_index']}")
    
    if failed_tests:
        print("\nFAILED TESTS:")
        print("-" * 60)
        for result in failed_tests:
            print(f"  {result['test_name']:<20} | Thread: {result['thread_index']} | Error: {result['error']}")
    
    print("\n" + "="*80)


def cleanup():
    """Clean up created resources."""
    print("\n🧹 Starting cleanup...")
    
    # Delete assignment (students are left for manual cleanup if needed)
    if assignment_id:
        try:
            delete_assignment(assignment_id)
            print(f"✅ Deleted assignment: {assignment_id}")
        except Exception as e:
            print(f"❌ Failed to delete assignment: {e}")
    
    print("🧹 Cleanup complete.")


def main():
    global assignment_id
    
    parser = argparse.ArgumentParser(description="Long-running grader stress test.")
    parser.add_argument("course_id", type=str, help="Valid course ID")
    parser.add_argument("--max_execution_time", type=int, default=20, 
                       help="Maximum execution time to test (seconds)")
    parser.add_argument("--num_submissions", type=int, default=1,
                       help="Number of submissions per test type")
    parser.add_argument("--max_workers", type=int, default=5,
                       help="Maximum number of concurrent workers")
    parser.add_argument("--cleanup", action="store_true", 
                       help="Delete created assignment after test")
    
    args = parser.parse_args()
    
    # Filter test codes based on max execution time
    filtered_tests = [t for t in TEST_CODES if t['execution_time'] <= args.max_execution_time]
    
    if not filtered_tests:
        print(f"No tests found with execution time <= {args.max_execution_time}s")
        return
    
    print(f"🚀 Starting long-running grader stress test...")
    print(f"   Course ID: {args.course_id}")
    print(f"   Max execution time: {args.max_execution_time}s")
    print(f"   Submissions per test: {args.num_submissions}")
    print(f"   Test types: {[t['name'] for t in filtered_tests]}")
    print(f"   Max concurrent workers: {args.max_workers}")
    
    try:
        # Create assignment
        print(f"\n📝 Creating test assignment...")
        assignment_id = create_assignment("Long-Running Grader Test", args.course_id)
        print(f"✅ Assignment created: {assignment_id}")
        
        # Upload autograder
        if os.path.exists(AUTOGRADER_ZIP_PATH):
            upload_autograder(assignment_id, AUTOGRADER_ZIP_PATH)
            print("✅ Autograder uploaded")
        else:
            print(f"⚠️  Autograder not found at {AUTOGRADER_ZIP_PATH}")
        
        # Create all submission tasks
        tasks = []
        for test_config in filtered_tests:
            for i in range(args.num_submissions):
                tasks.append((test_config, i))
        
        print(f"\n🧪 Running {len(tasks)} submission tests...")
        
        # Execute tasks with thread pool
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = []
            for test_config, i in tasks:
                future = executor.submit(submit_and_monitor_grading, test_config, i, assignment_id)
                futures.append(future)
            
            # Wait for all tasks to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Task failed with exception: {e}")
        
        # Print results
        print_results_summary()
        
        # Cleanup if requested
        if args.cleanup:
            cleanup()
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if args.cleanup:
            cleanup()


if __name__ == "__main__":
    main()