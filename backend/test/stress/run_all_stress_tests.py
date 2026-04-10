import argparse
import subprocess
import time
import sys
import os
from datetime import datetime
import json

"""
Comprehensive stress test runner that executes all stress tests in sequence.

This script runs all the stress tests for the backend system and provides
a consolidated report of all test results.

Usage:
    python run_all_stress_tests.py <course_id> [--quick] [--cleanup]

Example:
    python run_all_stress_tests.py 123e4567-e89b-12d3-a456-426614174000 --cleanup
"""

class StressTestRunner:
    def __init__(self, course_id, quick_mode=False, cleanup=True):
        self.course_id = course_id
        self.quick_mode = quick_mode
        self.cleanup = cleanup
        self.test_results = []
        self.start_time = None
        self.end_time = None
    
    def run_test(self, test_name, script_path, args):
        """Run a single stress test and capture results."""
        print(f"\n{'='*60}")
        print(f"🧪 Running {test_name}")
        print(f"{'='*60}")
        
        # Prepare command
        cmd = [sys.executable, script_path, self.course_id] + args
        if self.cleanup:
            cmd.append("--cleanup")
        
        print(f"Command: {' '.join(cmd)}")
        print()
        
        # Run the test
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = result.returncode == 0
            
            test_result = {
                'test_name': test_name,
                'script_path': script_path,
                'duration': duration,
                'success': success,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'command': ' '.join(cmd)
            }
            
            self.test_results.append(test_result)
            
            if success:
                print(f"✅ {test_name} completed successfully in {duration:.2f}s")
            else:
                print(f"❌ {test_name} failed after {duration:.2f}s")
                print(f"Error output: {result.stderr}")
            
            # Print stdout for successful tests
            if success and result.stdout:
                print(result.stdout)
            
            return success
            
        except subprocess.TimeoutExpired:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"⏰ {test_name} timed out after {duration:.2f}s")
            
            test_result = {
                'test_name': test_name,
                'script_path': script_path,
                'duration': duration,
                'success': False,
                'return_code': -1,
                'stdout': "",
                'stderr': "Test timed out",
                'command': ' '.join(cmd)
            }
            
            self.test_results.append(test_result)
            return False
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"💥 {test_name} crashed: {e}")
            
            test_result = {
                'test_name': test_name,
                'script_path': script_path,
                'duration': duration,
                'success': False,
                'return_code': -2,
                'stdout': "",
                'stderr': str(e),
                'command': ' '.join(cmd)
            }
            
            self.test_results.append(test_result)
            return False
    
    def run_all_tests(self):
        """Run all stress tests in sequence."""
        self.start_time = time.time()
        
        print(f"🚀 Starting comprehensive stress test suite")
        print(f"Course ID: {self.course_id}")
        print(f"Quick mode: {self.quick_mode}")
        print(f"Cleanup enabled: {self.cleanup}")
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Define test configurations
        if self.quick_mode:
            test_configs = [
                ("Bulk Assignment Uploads", "test_bulk_assignment_uploads.py", 
                 ["--num_uploads", "10", "--max_workers", "4"]),
                ("Student Submissions", "upload_assignments.py", 
                 ["--num_threads", "5"]),
                ("Long-Running Grader", "test_long_running_grader.py", 
                 ["--max_execution_time", "10", "--num_submissions", "2"]),
                ("Concurrent Enrollment", "test_concurrent_enrollment.py", 
                 ["--num_threads", "3", "--operations_per_thread", "5"]),
                ("CRUD Operations", "test_concurrent_crud_operations.py", 
                 ["--num_threads", "4", "--operations_per_thread", "8"]),
            ]
        else:
            test_configs = [
                ("Bulk Assignment Uploads", "test_bulk_assignment_uploads.py", 
                 ["--num_uploads", "25", "--max_workers", "8", "--monitor_system"]),
                ("Student Submissions", "upload_assignments.py", 
                 ["--num_threads", "10"]),
                ("Assignment Creation", "create_assignments.py", 
                 ["10"]),
                ("Long-Running Grader", "test_long_running_grader.py", 
                 ["--max_execution_time", "20", "--num_submissions", "3", "--max_workers", "5"]),
                ("Concurrent Enrollment", "test_concurrent_enrollment.py", 
                 ["--num_threads", "8", "--operations_per_thread", "10"]),
                ("CRUD Operations (Courses)", "test_concurrent_crud_operations.py", 
                 ["--num_threads", "6", "--operations_per_thread", "15", "--test_type", "courses"]),
                ("CRUD Operations (Assignments)", "test_concurrent_crud_operations.py", 
                 ["--num_threads", "6", "--operations_per_thread", "15", "--test_type", "assignments"]),
                ("CRUD Operations (Mixed)", "test_concurrent_crud_operations.py", 
                 ["--num_threads", "8", "--operations_per_thread", "12", "--test_type", "mixed"]),
            ]
        
        # Run each test
        successful_tests = 0
        for test_name, script_path, args in test_configs:
            # Special handling for create_assignments.py which has different argument order
            if script_path == "create_assignments.py":
                cmd_args = [args[0], self.course_id] + args[1:]
                success = self.run_test(test_name, script_path, cmd_args)
            else:
                success = self.run_test(test_name, script_path, args)
            
            if success:
                successful_tests += 1
            
            # Allow rest
            time.sleep(2)
        
        self.end_time = time.time()
        
        self.print_summary()
        
        self.save_results()
    
    def print_summary(self):
        """Print a comprehensive summary of all test results."""
        total_duration = self.end_time - self.start_time
        successful_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = len(self.test_results) - successful_tests
        
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE STRESS TEST RESULTS SUMMARY")
        print(f"{'='*80}")
        print(f"Test Suite Duration: {total_duration:.2f}s ({total_duration/60:.1f} minutes)")
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Successful Tests: {successful_tests} ({successful_tests/len(self.test_results)*100:.1f}%)")
        print(f"Failed Tests: {failed_tests} ({failed_tests/len(self.test_results)*100:.1f}%)")
        print()
        
        # Individual test results
        print("INDIVIDUAL TEST RESULTS:")
        print("-" * 60)
        for result in self.test_results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            duration = result['duration']
            print(f"  {status} | {result['test_name']:<30} | {duration:6.2f}s")
        
        print()
        
        # Failed test details
        if failed_tests > 0:
            print("FAILED TEST DETAILS:")
            print("-" * 60)
            for result in self.test_results:
                if not result['success']:
                    print(f"  {result['test_name']}:")
                    print(f"    Return Code: {result['return_code']}")
                    print(f"    Error: {result['stderr'][:200]}...")
                    print()
        
        # Performance insights
        test_durations = [r['duration'] for r in self.test_results if r['success']]
        if test_durations:
            avg_duration = sum(test_durations) / len(test_durations)
            max_duration = max(test_durations)
            min_duration = min(test_durations)
            
            print("PERFORMANCE SUMMARY:")
            print(f"  Average test duration: {avg_duration:.2f}s")
            print(f"  Longest test: {max_duration:.2f}s")
            print(f"  Shortest test: {min_duration:.2f}s")
            print()
        
        # Overall assessment
        print("OVERALL ASSESSMENT:")
        if successful_tests == len(self.test_results):
            print("  🎉 All stress tests passed! System appears to handle load well.")
        elif successful_tests >= len(self.test_results) * 0.8:
            print("  ⚠️  Most tests passed, but some issues detected. Review failed tests.")
        else:
            print("  🚨 Multiple test failures detected. System may have performance issues.")
        
        print(f"\n{'='*80}")
    
    def save_results(self):
        """Save detailed test results to a JSON file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"stress_test_results_{timestamp}.json"
        
        results_data = {
            'test_suite_info': {
                'course_id': self.course_id,
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'end_time': datetime.fromtimestamp(self.end_time).isoformat(),
                'total_duration': self.end_time - self.start_time,
                'quick_mode': self.quick_mode,
                'cleanup_enabled': self.cleanup
            },
            'summary': {
                'total_tests': len(self.test_results),
                'successful_tests': sum(1 for r in self.test_results if r['success']),
                'failed_tests': sum(1 for r in self.test_results if not r['success'])
            },
            'test_results': self.test_results
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(results_data, f, indent=2)
            print(f"📄 Detailed results saved to: {filename}")
        except Exception as e:
            print(f"⚠️  Failed to save results file: {e}")


def main():
    parser = argparse.ArgumentParser(description="Comprehensive stress test runner.")
    parser.add_argument("course_id", type=str, help="Valid course ID for all tests")
    parser.add_argument("--quick", action="store_true", 
                       help="Run tests with reduced load for faster execution")
    parser.add_argument("--cleanup", action="store_true", default=True,
                       help="Clean up created resources after each test (default: True)")
    parser.add_argument("--no-cleanup", action="store_false", dest="cleanup",
                       help="Don't clean up created resources")
    
    args = parser.parse_args()
    
    # Ensure that test scripts exist
    required_scripts = [
        "test_bulk_assignment_uploads.py",
        "upload_assignments.py", 
        "create_assignments.py",
        "test_long_running_grader.py",
        "test_concurrent_enrollment.py",
        "test_concurrent_crud_operations.py",
        "utils.py"
    ]
    
    missing_scripts = []
    for script in required_scripts:
        if not os.path.exists(script):
            missing_scripts.append(script)
    
    if missing_scripts:
        print(f"❌ Missing required test scripts:")
        for script in missing_scripts:
            print(f"   - {script}")
        print("\nPlease ensure all stress test scripts are in the current directory.")
        sys.exit(1)
    
    # Run the tests
    runner = StressTestRunner(args.course_id, args.quick, args.cleanup)
    runner.run_all_tests()


if __name__ == "__main__":
    main()