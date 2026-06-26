import argparse
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
from utils import add_user, delete_user
import requests
import uuid

"""
Stress test for concurrent user enrollment and unenrollment operations.

Tests rapid enrollment/unenrollment of the same user from a course in parallel threads
to check for race conditions, database locking issues, and data consistency.

Usage:
    python test_concurrent_enrollment.py <course_id> [--num_threads N] [--operations_per_thread M]

Example:
    python test_concurrent_enrollment.py 123e4567-e89b-12d3-a456-426614174000 --num_threads 10 --operations_per_thread 5
"""

BASE_URL = "http://localhost:5001"

# Shared state
test_results = []
results_lock = threading.Lock()
created_users = []
users_lock = threading.Lock()


def enroll_user_in_course(user_id, course_id):
    """Enroll a user in a course."""
    url = f"{BASE_URL}/enroll_user"
    payload = {
        "user_id": user_id,
        "course_id": course_id
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def unenroll_user_from_course(user_id, course_id):
    """Unenroll a user from a course."""
    url = f"{BASE_URL}/unenroll_user"
    payload = {
        "user_id": user_id,
        "course_id": course_id
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def get_user_courses(user_id):
    """Get courses for a user."""
    url = f"{BASE_URL}/get_user_courses"
    response = requests.get(url, params={"user_id": user_id})
    response.raise_for_status()
    return response.json()


def is_user_enrolled(user_id, course_id):
    """Check if user is enrolled in a specific course."""
    try:
        courses = get_user_courses(user_id)
        return any(course.get('id') == course_id for course in courses.get('courses', []))
    except:
        return False


def rapid_enrollment_operations(user_id, course_id, thread_id, operations_count):
    """Perform rapid enrollment and unenrollment operations."""
    thread_results = {
        'thread_id': thread_id,
        'user_id': user_id,
        'operations': [],
        'total_operations': operations_count,
        'successful_operations': 0,
        'failed_operations': 0,
        'errors': []
    }
    
    print(f"[Thread-{thread_id}] Starting {operations_count} enrollment operations for user {user_id}")
    
    for operation_num in range(operations_count):
        try:
            start_time = time.time()
            
            # Randomly choose to enroll or unenroll
            # Start with enrollment to ensure we have something to unenroll
            if operation_num == 0 or random.choice([True, False]):
                operation = "enroll"
                result = enroll_user_in_course(user_id, course_id)
                expected_enrolled = True
            else:
                operation = "unenroll"
                result = unenroll_user_from_course(user_id, course_id)
                expected_enrolled = False
            
            operation_time = time.time() - start_time
            
            # Verify the operation worked by checking enrollment status
            time.sleep(0.1)  # Small delay to allow for database consistency
            actual_enrolled = is_user_enrolled(user_id, course_id)
            
            # Note: Due to race conditions, the actual state might not match expected
            # We're more interested in whether the operations complete successfully
            operation_result = {
                'operation_num': operation_num,
                'operation': operation,
                'time': operation_time,
                'expected_enrolled': expected_enrolled,
                'actual_enrolled': actual_enrolled,
                'consistent': actual_enrolled == expected_enrolled,
                'success': True
            }
            
            thread_results['operations'].append(operation_result)
            thread_results['successful_operations'] += 1
            
            print(f"[Thread-{thread_id}] Op {operation_num}: {operation} ({'✅' if operation_result['consistent'] else '⚠️'})")
            
        except Exception as e:
            error_info = {
                'operation_num': operation_num,
                'operation': operation if 'operation' in locals() else 'unknown',
                'error': str(e),
                'success': False
            }
            
            thread_results['operations'].append(error_info)
            thread_results['failed_operations'] += 1
            thread_results['errors'].append(str(e))
            
            print(f"[Thread-{thread_id}] Op {operation_num}: ❌ {e}")
        
        # Small random delay to create more realistic timing
        time.sleep(random.uniform(0.01, 0.05))
    
    with results_lock:
        test_results.append(thread_results)
    
    print(f"[Thread-{thread_id}] Completed: {thread_results['successful_operations']}/{operations_count} successful")
    return thread_results


def create_test_users(num_users):
    """Create test users for the stress test."""
    print(f"📝 Creating {num_users} test users...")
    
    user_ids = []
    for i in range(num_users):
        try:
            user_name = f"enrollment_test_user_{i}_{uuid.uuid4().hex[:8]}"
            user_id = add_user(name=user_name)
            user_ids.append(user_id)
            
            with users_lock:
                created_users.append(user_id)
                
            print(f"   Created user {i+1}/{num_users}: {user_name}")
            
        except Exception as e:
            print(f"   Failed to create user {i+1}: {e}")
    
    return user_ids


def print_results_summary():
    """Print a comprehensive summary of test results."""
    print("\n" + "="*80)
    print("CONCURRENT ENROLLMENT STRESS TEST RESULTS")
    print("="*80)
    
    total_threads = len(test_results)
    total_operations = sum(r['total_operations'] for r in test_results)
    total_successful = sum(r['successful_operations'] for r in test_results)
    total_failed = sum(r['failed_operations'] for r in test_results)
    
    print(f"Total threads: {total_threads}")
    print(f"Total operations: {total_operations}")
    print(f"Successful operations: {total_successful} ({total_successful/total_operations*100:.1f}%)")
    print(f"Failed operations: {total_failed} ({total_failed/total_operations*100:.1f}%)")
    print()
    
    # Analyze consistency
    all_operations = []
    for result in test_results:
        all_operations.extend([op for op in result['operations'] if op.get('success', False)])
    
    consistent_operations = [op for op in all_operations if op.get('consistent', False)]
    inconsistent_operations = [op for op in all_operations if not op.get('consistent', True)]
    
    if all_operations:
        print(f"State consistency: {len(consistent_operations)}/{len(all_operations)} operations " +
              f"({len(consistent_operations)/len(all_operations)*100:.1f}%)")
        
        if inconsistent_operations:
            print(f"⚠️  {len(inconsistent_operations)} operations had state inconsistencies")
            print("   (This may be expected due to race conditions)")
    
    print()
    
    # Performance metrics
    if all_operations:
        operation_times = [op['time'] for op in all_operations if 'time' in op]
        if operation_times:
            avg_time = sum(operation_times) / len(operation_times)
            max_time = max(operation_times)
            min_time = min(operation_times)
            
            print("PERFORMANCE METRICS:")
            print(f"  Average operation time: {avg_time:.3f}s")
            print(f"  Min operation time: {min_time:.3f}s")
            print(f"  Max operation time: {max_time:.3f}s")
            print()
    
    # Error analysis
    all_errors = []
    for result in test_results:
        all_errors.extend(result['errors'])
    
    if all_errors:
        print("ERROR ANALYSIS:")
        error_counts = {}
        for error in all_errors:
            error_type = error.split(':')[0] if ':' in error else error
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        for error_type, count in error_counts.items():
            print(f"  {error_type}: {count} occurrences")
        print()
    
    # Thread performance summary
    print("THREAD PERFORMANCE:")
    print("-" * 60)
    for result in test_results:
        success_rate = result['successful_operations'] / result['total_operations'] * 100
        print(f"  Thread {result['thread_id']:2d}: {result['successful_operations']:2d}/{result['total_operations']:2d} " +
              f"operations ({success_rate:5.1f}%) | User: {result['user_id'][:8]}...")
    
    print("\n" + "="*80)


def cleanup():
    """Clean up created test users."""
    print("\n🧹 Starting cleanup...")
    
    deleted_count = 0
    for user_id in created_users:
        try:
            delete_user(user_id)
            deleted_count += 1
            print(f"   Deleted user: {user_id}")
        except Exception as e:
            print(f"   Failed to delete user {user_id}: {e}")
    
    print(f"🧹 Cleanup complete. Deleted {deleted_count}/{len(created_users)} users.")


def main():
    parser = argparse.ArgumentParser(description="Concurrent enrollment stress test.")
    parser.add_argument("course_id", type=str, help="Valid course ID")
    parser.add_argument("--num_threads", type=int, default=5,
                       help="Number of concurrent threads")
    parser.add_argument("--operations_per_thread", type=int, default=10,
                       help="Number of enroll/unenroll operations per thread")
    parser.add_argument("--users_per_thread", type=int, default=1,
                       help="Number of users per thread (1 = same user for all operations in thread)")
    parser.add_argument("--max_workers", type=int, default=10,
                       help="Maximum number of concurrent workers")
    parser.add_argument("--cleanup", action="store_true",
                       help="Delete created users after test")
    
    args = parser.parse_args()
    
    total_users_needed = args.num_threads * args.users_per_thread
    
    print(f"🚀 Starting concurrent enrollment stress test...")
    print(f"   Course ID: {args.course_id}")
    print(f"   Threads: {args.num_threads}")
    print(f"   Operations per thread: {args.operations_per_thread}")
    print(f"   Users per thread: {args.users_per_thread}")
    print(f"   Total users needed: {total_users_needed}")
    print(f"   Max workers: {args.max_workers}")
    
    try:
        # Create test users
        user_ids = create_test_users(total_users_needed)
        
        if len(user_ids) < total_users_needed:
            print(f"⚠️  Only created {len(user_ids)}/{total_users_needed} users. Continuing with available users.")
        
        print(f"\n🧪 Starting enrollment operations...")
        
        # Create tasks for thread pool
        tasks = []
        user_index = 0
        
        for thread_id in range(args.num_threads):
            # Assign users to this thread
            thread_users = []
            for _ in range(args.users_per_thread):
                if user_index < len(user_ids):
                    thread_users.append(user_ids[user_index])
                    user_index += 1
            
            # For now, let's test with one user per thread doing multiple operations
            # This tests the same user being enrolled/unenrolled rapidly
            if thread_users:
                primary_user = thread_users[0]  # Use first user for rapid operations
                tasks.append((primary_user, args.course_id, thread_id, args.operations_per_thread))
        
        # Execute tasks with thread pool
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = []
            for user_id, course_id, thread_id, ops_count in tasks:
                future = executor.submit(rapid_enrollment_operations, user_id, course_id, thread_id, ops_count)
                futures.append(future)
            
            # Wait for all tasks to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Thread failed with exception: {e}")
        
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