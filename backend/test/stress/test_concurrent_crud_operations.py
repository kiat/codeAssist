"""
Stress test for concurrent CRUD operations on courses and assignments.

Tests creating and deleting courses/assignments while other threads are 
querying or modifying them to check for race conditions and data consistency.

Usage:
    python test_concurrent_crud_operations.py [--num_threads N] [--operations_per_thread M] [--test_type TYPE]

Example:
    python test_concurrent_crud_operations.py --num_threads 8 --operations_per_thread 5 --test_type both
"""

import argparse
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import uuid
import requests
from utils import create_assignment, delete_assignment, add_user

BASE_URL = "http://localhost:5001"

# Shared state
test_results = []
results_lock = threading.Lock()
created_courses = []
courses_lock = threading.Lock()
created_assignments = []
assignments_lock = threading.Lock()
active_resources = {
    'courses': set(),
    'assignments': set()
}
resources_lock = threading.Lock()


def create_course(name, instructor_id=None):
    """Create a course."""
    if instructor_id is None:
        # Create a temporary instructor if none provided
        instructor_id = add_user(name=f"instructor_{uuid.uuid4().hex[:8]}", role="Instructor")
    
    url = f"{BASE_URL}/create_course"
    payload = {
        "name": name,
        "instructor_id": instructor_id
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()["id"]


def delete_course(course_id):
    """Delete a course."""
    url = f"{BASE_URL}/delete_course"
    response = requests.delete(url, params={"course_id": course_id})
    response.raise_for_status()
    return response.json()


def get_course(course_id):
    """Get course details."""
    url = f"{BASE_URL}/get_course"
    response = requests.get(url, params={"course_id": course_id})
    response.raise_for_status()
    return response.json()


def get_course_assignments(course_id):
    """Get assignments for a course."""
    url = f"{BASE_URL}/get_course_assignments"
    response = requests.get(url, params={"course_id": course_id})
    response.raise_for_status()
    return response.json()


def get_assignment(assignment_id):
    """Get assignment details."""
    url = f"{BASE_URL}/get_assignment"
    response = requests.get(url, params={"assignment_id": assignment_id})
    response.raise_for_status()
    return response.json()


class ConcurrentCRUDTester:
    def __init__(self, thread_id):
        self.thread_id = thread_id
        self.operations = []
        self.successful_operations = 0
        self.failed_operations = 0
        self.errors = []
    
    def log_operation(self, operation_type, success, duration, details=None, error=None):
        """Log an operation result."""
        operation = {
            'type': operation_type,
            'success': success,
            'duration': duration,
            'details': details or {},
            'error': error,
            'timestamp': time.time()
        }
        self.operations.append(operation)
        
        if success:
            self.successful_operations += 1
            print(f"[Thread-{self.thread_id}] ✅ {operation_type}: {details}")
        else:
            self.failed_operations += 1
            print(f"[Thread-{self.thread_id}] ❌ {operation_type}: {error}")
    
    def create_course_operation(self):
        """Perform a create course operation."""
        start_time = time.time()
        try:
            course_name = f"Course_T{self.thread_id}_{uuid.uuid4().hex[:8]}"
            course_id = create_course(course_name)
            
            # Track created course
            with courses_lock:
                created_courses.append(course_id)
            
            with resources_lock:
                active_resources['courses'].add(course_id)
            
            duration = time.time() - start_time
            self.log_operation("CREATE_COURSE", True, duration, 
                             {"course_id": course_id, "name": course_name})
            return course_id
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_operation("CREATE_COURSE", False, duration, error=str(e))
            return None
    
    def delete_course_operation(self, course_id):
        """Perform a delete course operation."""
        start_time = time.time()
        try:
            delete_course(course_id)
            
            with resources_lock:
                active_resources['courses'].discard(course_id)
            
            duration = time.time() - start_time
            self.log_operation("DELETE_COURSE", True, duration, {"course_id": course_id})
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_operation("DELETE_COURSE", False, duration, error=str(e))
            return False
    
    def query_course_operation(self, course_id):
        """Perform a query course operation."""
        start_time = time.time()
        try:
            course_data = get_course(course_id)
            duration = time.time() - start_time
            self.log_operation("QUERY_COURSE", True, duration, 
                             {"course_id": course_id, "name": course_data.get('name')})
            return course_data
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_operation("QUERY_COURSE", False, duration, error=str(e))
            return None
    
    def create_assignment_operation(self, course_id):
        """Perform a create assignment operation."""
        start_time = time.time()
        try:
            assignment_name = f"Assignment_T{self.thread_id}_{uuid.uuid4().hex[:8]}"
            assignment_id = create_assignment(assignment_name, course_id)
            
            # Track created assignment
            with assignments_lock:
                created_assignments.append(assignment_id)
            
            with resources_lock:
                active_resources['assignments'].add(assignment_id)
            
            duration = time.time() - start_time
            self.log_operation("CREATE_ASSIGNMENT", True, duration,
                             {"assignment_id": assignment_id, "name": assignment_name, "course_id": course_id})
            return assignment_id
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_operation("CREATE_ASSIGNMENT", False, duration, error=str(e))
            return None
    
    def delete_assignment_operation(self, assignment_id):
        """Perform a delete assignment operation."""
        start_time = time.time()
        try:
            delete_assignment(assignment_id)
            
            with resources_lock:
                active_resources['assignments'].discard(assignment_id)
            
            duration = time.time() - start_time
            self.log_operation("DELETE_ASSIGNMENT", True, duration, {"assignment_id": assignment_id})
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_operation("DELETE_ASSIGNMENT", False, duration, error=str(e))
            return False
    
    def query_assignment_operation(self, assignment_id):
        """Perform a query assignment operation."""
        start_time = time.time()
        try:
            assignment_data = get_assignment(assignment_id)
            duration = time.time() - start_time
            self.log_operation("QUERY_ASSIGNMENT", True, duration,
                             {"assignment_id": assignment_id, "name": assignment_data.get('name')})
            return assignment_data
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_operation("QUERY_ASSIGNMENT", False, duration, error=str(e))
            return None
    
    def query_course_assignments_operation(self, course_id):
        """Perform a query course assignments operation."""
        start_time = time.time()
        try:
            assignments = get_course_assignments(course_id)
            duration = time.time() - start_time
            assignment_count = len(assignments.get('assignments', []))
            self.log_operation("QUERY_COURSE_ASSIGNMENTS", True, duration,
                             {"course_id": course_id, "assignment_count": assignment_count})
            return assignments
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_operation("QUERY_COURSE_ASSIGNMENTS", False, duration, error=str(e))
            return None


def run_course_crud_operations(thread_id, operations_count):
    """Run CRUD operations focused on courses."""
    tester = ConcurrentCRUDTester(thread_id)
    local_courses = []
    
    print(f"[Thread-{thread_id}] Starting {operations_count} course CRUD operations")
    
    for i in range(operations_count):
        try:
            # Choose operation type based on current state
            if not local_courses or random.random() < 0.4:  # 40% chance to create
                course_id = tester.create_course_operation()
                if course_id:
                    local_courses.append(course_id)
            
            elif local_courses and random.random() < 0.3:  # 30% chance to delete
                course_id = random.choice(local_courses)
                success = tester.delete_course_operation(course_id)
                if success:
                    local_courses.remove(course_id)
            
            else:  # Query operations
                # Get a course to query (could be from any thread)
                with resources_lock:
                    available_courses = list(active_resources['courses'])
                
                if available_courses:
                    course_id = random.choice(available_courses)
                    if random.choice([True, False]):
                        tester.query_course_operation(course_id)
                    else:
                        tester.query_course_assignments_operation(course_id)
            
            # Random delay to simulate real-world timing
            time.sleep(random.uniform(0.01, 0.1))
            
        except Exception as e:
            print(f"[Thread-{thread_id}] Unexpected error in operation {i}: {e}")
    
    # Store results
    results = {
        'thread_id': thread_id,
        'test_type': 'course_crud',
        'total_operations': operations_count,
        'successful_operations': tester.successful_operations,
        'failed_operations': tester.failed_operations,
        'operations': tester.operations,
        'errors': tester.errors,
        'local_resources_created': len(local_courses)
    }
    
    with results_lock:
        test_results.append(results)
    
    print(f"[Thread-{thread_id}] Course CRUD completed: {tester.successful_operations}/{operations_count} successful")
    return results


def run_assignment_crud_operations(thread_id, operations_count):
    """Run CRUD operations focused on assignments."""
    tester = ConcurrentCRUDTester(thread_id)
    local_assignments = []
    
    print(f"[Thread-{thread_id}] Starting {operations_count} assignment CRUD operations")
    
    # First, ensure we have at least one course to work with
    initial_course = tester.create_course_operation()
    if not initial_course:
        print(f"[Thread-{thread_id}] Failed to create initial course, aborting assignment operations")
        return
    
    for i in range(operations_count):
        try:
            # Get available courses for assignment operations
            with resources_lock:
                available_courses = list(active_resources['courses'])
            
            if not available_courses:
                # Create a course if none available
                course_id = tester.create_course_operation()
                if course_id:
                    available_courses = [course_id]
            
            if available_courses:
                # Choose operation type
                if not local_assignments or random.random() < 0.4:  # 40% chance to create
                    course_id = random.choice(available_courses)
                    assignment_id = tester.create_assignment_operation(course_id)
                    if assignment_id:
                        local_assignments.append(assignment_id)
                
                elif local_assignments and random.random() < 0.3:  # 30% chance to delete
                    assignment_id = random.choice(local_assignments)
                    success = tester.delete_assignment_operation(assignment_id)
                    if success:
                        local_assignments.remove(assignment_id)
                
                else:  # Query operations
                    with resources_lock:
                        available_assignments = list(active_resources['assignments'])
                    
                    if available_assignments:
                        assignment_id = random.choice(available_assignments)
                        tester.query_assignment_operation(assignment_id)
            
            # Random delay
            time.sleep(random.uniform(0.01, 0.1))
            
        except Exception as e:
            print(f"[Thread-{thread_id}] Unexpected error in assignment operation {i}: {e}")
    
    # Store results
    results = {
        'thread_id': thread_id,
        'test_type': 'assignment_crud',
        'total_operations': operations_count,
        'successful_operations': tester.successful_operations,
        'failed_operations': tester.failed_operations,
        'operations': tester.operations,
        'errors': tester.errors,
        'local_resources_created': len(local_assignments)
    }
    
    with results_lock:
        test_results.append(results)
    
    print(f"[Thread-{thread_id}] Assignment CRUD completed: {tester.successful_operations}/{operations_count} successful")
    return results


def run_mixed_crud_operations(thread_id, operations_count):
    """Run mixed CRUD operations on both courses and assignments."""
    tester = ConcurrentCRUDTester(thread_id)
    local_courses = []
    local_assignments = []
    
    print(f"[Thread-{thread_id}] Starting {operations_count} mixed CRUD operations")
    
    for i in range(operations_count):
        try:
            # Choose between course and assignment operations
            if random.choice([True, False]):  # Course operations
                if not local_courses or random.random() < 0.3:
                    course_id = tester.create_course_operation()
                    if course_id:
                        local_courses.append(course_id)
                elif local_courses and random.random() < 0.2:
                    course_id = random.choice(local_courses)
                    success = tester.delete_course_operation(course_id)
                    if success:
                        local_courses.remove(course_id)
                else:
                    with resources_lock:
                        available_courses = list(active_resources['courses'])
                    if available_courses:
                        course_id = random.choice(available_courses)
                        tester.query_course_operation(course_id)
            
            else:  # Assignment operations
                with resources_lock:
                    available_courses = list(active_resources['courses'])
                
                if available_courses:
                    if not local_assignments or random.random() < 0.3:
                        course_id = random.choice(available_courses)
                        assignment_id = tester.create_assignment_operation(course_id)
                        if assignment_id:
                            local_assignments.append(assignment_id)
                    elif local_assignments and random.random() < 0.2:
                        assignment_id = random.choice(local_assignments)
                        success = tester.delete_assignment_operation(assignment_id)
                        if success:
                            local_assignments.remove(assignment_id)
                    else:
                        with resources_lock:
                            available_assignments = list(active_resources['assignments'])
                        if available_assignments:
                            assignment_id = random.choice(available_assignments)
                            tester.query_assignment_operation(assignment_id)
            
            # Delay
            time.sleep(random.uniform(0.01, 0.1))
            
        except Exception as e:
            print(f"[Thread-{thread_id}] Unexpected error in mixed operation {i}: {e}")
    
    # Store results
    results = {
        'thread_id': thread_id,
        'test_type': 'mixed_crud',
        'total_operations': operations_count,
        'successful_operations': tester.successful_operations,
        'failed_operations': tester.failed_operations,
        'operations': tester.operations,
        'errors': tester.errors,
        'local_resources_created': len(local_courses) + len(local_assignments)
    }
    
    with results_lock:
        test_results.append(results)
    
    print(f"[Thread-{thread_id}] Mixed CRUD completed: {tester.successful_operations}/{operations_count} successful")
    return results


def print_results_summary():
    """Print comprehensive test results."""
    print("\n" + "="*80)
    print("CONCURRENT CRUD OPERATIONS STRESS TEST RESULTS")
    print("="*80)
    
    if not test_results:
        print("No test results available.")
        return
    
    # Overall statistics
    total_threads = len(test_results)
    total_operations = sum(r['total_operations'] for r in test_results)
    total_successful = sum(r['successful_operations'] for r in test_results)
    total_failed = sum(r['failed_operations'] for r in test_results)
    
    print(f"Total threads: {total_threads}")
    print(f"Total operations: {total_operations}")
    print(f"Successful operations: {total_successful} ({total_successful/total_operations*100:.1f}%)")
    print(f"Failed operations: {total_failed} ({total_failed/total_operations*100:.1f}%)")
    print()
    
    # Operation type analysis
    operation_stats = {}
    all_operations = []
    
    for result in test_results:
        for op in result['operations']:
            op_type = op['type']
            if op_type not in operation_stats:
                operation_stats[op_type] = {'total': 0, 'successful': 0, 'failed': 0, 'avg_duration': 0}
            
            operation_stats[op_type]['total'] += 1
            if op['success']:
                operation_stats[op_type]['successful'] += 1
            else:
                operation_stats[op_type]['failed'] += 1
            
            all_operations.append(op)
    
    # Calculate average durations
    for op_type in operation_stats:
        durations = [op['duration'] for op in all_operations if op['type'] == op_type]
        if durations:
            operation_stats[op_type]['avg_duration'] = sum(durations) / len(durations)
    
    print("OPERATION TYPE ANALYSIS:")
    print("-" * 60)
    for op_type, stats in operation_stats.items():
        success_rate = stats['successful'] / stats['total'] * 100 if stats['total'] > 0 else 0
        print(f"  {op_type:<20} | {stats['successful']:3d}/{stats['total']:3d} " +
              f"({success_rate:5.1f}%) | Avg: {stats['avg_duration']:.3f}s")
    
    print()
    
    # Resource creation summary
    with resources_lock:
        final_courses = len(active_resources['courses'])
        final_assignments = len(active_resources['assignments'])
    
    total_courses_created = len(created_courses)
    total_assignments_created = len(created_assignments)
    
    print("RESOURCE SUMMARY:")
    print(f"  Courses created: {total_courses_created} | Still active: {final_courses}")
    print(f"  Assignments created: {total_assignments_created} | Still active: {final_assignments}")
    print()
    
    # Error analysis
    all_errors = []
    for result in test_results:
        all_errors.extend(result['errors'])
    
    if all_errors:
        print("ERROR ANALYSIS:")
        error_counts = {}
        for error in all_errors:
            error_type = error.split(':')[0] if ':' in error else error[:50]
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count} occurrences")
        print()
    
    # Thread performance
    print("THREAD PERFORMANCE:")
    print("-" * 60)
    for result in test_results:
        success_rate = result['successful_operations'] / result['total_operations'] * 100
        print(f"  Thread {result['thread_id']:2d} ({result['test_type']:<12}) | " +
              f"{result['successful_operations']:2d}/{result['total_operations']:2d} " +
              f"({success_rate:5.1f}%) | Resources created: {result.get('local_resources_created', 0)}")
    
    print("\n" + "="*80)


def cleanup():
    """Clean up created resources."""
    print("\n🧹 Starting cleanup...")
    
    # Delete assignments first (they depend on courses)
    deleted_assignments = 0
    for assignment_id in created_assignments:
        try:
            delete_assignment(assignment_id)
            deleted_assignments += 1
            print(f"   Deleted assignment: {assignment_id}")
        except Exception as e:
            print(f"   Failed to delete assignment {assignment_id}: {e}")
    
    # Delete courses
    deleted_courses = 0
    for course_id in created_courses:
        try:
            delete_course(course_id)
            deleted_courses += 1
            print(f"   Deleted course: {course_id}")
        except Exception as e:
            print(f"   Failed to delete course {course_id}: {e}")
    
    print(f"🧹 Cleanup complete. Deleted {deleted_courses}/{len(created_courses)} courses, " +
          f"{deleted_assignments}/{len(created_assignments)} assignments.")


def main():
    parser = argparse.ArgumentParser(description="Concurrent CRUD operations stress test.")
    parser.add_argument("--num_threads", type=int, default=6,
                       help="Number of concurrent threads")
    parser.add_argument("--operations_per_thread", type=int, default=15,
                       help="Number of operations per thread")
    parser.add_argument("--test_type", choices=['courses', 'assignments', 'mixed', 'both'], 
                       default='both', help="Type of operations to test")
    parser.add_argument("--max_workers", type=int, default=10,
                       help="Maximum number of concurrent workers")
    parser.add_argument("--cleanup", action="store_true",
                       help="Delete created resources after test")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting concurrent CRUD operations stress test...")
    print(f"   Threads: {args.num_threads}")
    print(f"   Operations per thread: {args.operations_per_thread}")
    print(f"   Test type: {args.test_type}")
    print(f"   Max workers: {args.max_workers}")
    
    try:
        # Prepare tasks based on test type
        tasks = []
        
        if args.test_type in ['courses', 'both']:
            # Add course-focused threads
            thread_count = args.num_threads if args.test_type == 'courses' else args.num_threads // 2
            for i in range(thread_count):
                tasks.append((run_course_crud_operations, i, args.operations_per_thread))
        
        if args.test_type in ['assignments', 'both']:
            # Add assignment-focused threads
            start_id = 0 if args.test_type == 'assignments' else args.num_threads // 2
            thread_count = args.num_threads if args.test_type == 'assignments' else args.num_threads - args.num_threads // 2
            for i in range(thread_count):
                tasks.append((run_assignment_crud_operations, start_id + i, args.operations_per_thread))
        
        if args.test_type == 'mixed':
            for i in range(args.num_threads):
                tasks.append((run_mixed_crud_operations, i, args.operations_per_thread))
        
        print(f"\n🧪 Starting {len(tasks)} test threads...")
        
        # Execute tasks
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = []
            for func, thread_id, ops_count in tasks:
                future = executor.submit(func, thread_id, ops_count)
                futures.append(future)
            
            # Wait for completion
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