import argparse
import os
import time
import threading
import psutil
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Any
import uuid
import tempfile
import zipfile
from utils import create_assignment, upload_autograder, delete_assignment, add_user

"""
Enhanced stress test for bulk assignment uploads with comprehensive metrics.

This test evaluates the system's performance under load when handling multiple
assignment uploads concurrently. It measures upload success rate, request times,
and provides detailed performance analysis.

Usage:
    python test_bulk_assignment_uploads.py <course_id> [--num_uploads N] [--max_workers M]

Example:
    python test_bulk_assignment_uploads.py 123e4567-e89b-12d3-a456-426614174000 --num_uploads 25 --max_workers 10
"""

AUTOGRADER_ZIP_PATH = os.path.abspath(os.path.join("..", "..", "assignment-examples", "A1", "A1.zip"))

@dataclass
class UploadMetrics:
    """Metrics for a single upload operation."""
    assignment_id: str
    thread_id: int
    start_time: float
    end_time: float
    duration: float
    success: bool
    error: str = None
    file_size: int = 0
    upload_speed_mbps: float = 0.0


class SystemMonitor:
    """Monitor system resources during the test."""
    
    def __init__(self):
        self.monitoring = False
        self.metrics = []
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start system resource monitoring."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop system resource monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk_io = psutil.disk_io_counters()
                net_io = psutil.net_io_counters()
                
                metric = {
                    'timestamp': time.time(),
                    'cpu_percent': cpu_percent,
                    'memory_percent': memory.percent,
                    'memory_used_mb': memory.used / 1024 / 1024,
                    'disk_read_mb': disk_io.read_bytes / 1024 / 1024 if disk_io else 0,
                    'disk_write_mb': disk_io.write_bytes / 1024 / 1024 if disk_io else 0,
                    'network_sent_mb': net_io.bytes_sent / 1024 / 1024 if net_io else 0,
                    'network_recv_mb': net_io.bytes_recv / 1024 / 1024 if net_io else 0,
                }
                
                self.metrics.append(metric)
                time.sleep(1)
                
            except Exception as e:
                print(f"⚠️  Monitoring error: {e}")
                time.sleep(1)
    
    def get_peak_metrics(self):
        """Get peak resource usage metrics."""
        if not self.metrics:
            return {}
        
        return {
            'peak_cpu_percent': max(m['cpu_percent'] for m in self.metrics),
            'peak_memory_percent': max(m['memory_percent'] for m in self.metrics),
            'peak_memory_used_mb': max(m['memory_used_mb'] for m in self.metrics),
            'avg_cpu_percent': statistics.mean(m['cpu_percent'] for m in self.metrics),
            'avg_memory_percent': statistics.mean(m['memory_percent'] for m in self.metrics),
        }


def create_test_zip_file(size_mb=1):
    """Create a test zip file of specified size."""
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
        with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Create a dummy file to reach desired size
            dummy_content = b'0' * (1024 * 1024)
            
            for i in range(size_mb):
                zipf.writestr(f'dummy_file_{i}.txt', dummy_content)
            
            # Add some realistic autograder files
            zipf.writestr('run_tests.py', '''
import subprocess
import sys

def run_tests():
    """Run the autograder tests."""
    try:
        result = subprocess.run([sys.executable, 'test_calculator.py'], 
                               capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("All tests passed!")
            return True
        else:
            print("Tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("Tests timed out!")
        return False
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
''')
            
            zipf.writestr('test_calculator.py', '''
import unittest

class TestCalculator(unittest.TestCase):
    def test_addition(self):
        # Simple test
        self.assertEqual(2 + 2, 4)
    
    def test_subtraction(self):
        self.assertEqual(5 - 3, 2)

if __name__ == '__main__':
    unittest.main()
''')
        
        return temp_zip.name


def upload_assignment_with_metrics(thread_id: int, course_id: str, upload_index: int, 
                                 zip_file_path: str) -> UploadMetrics:
    """Upload a single assignment and collect metrics."""
    start_time = time.time()
    
    try:
        # Create assignment
        assignment_name = f"BulkUpload_T{thread_id}_{upload_index}_{uuid.uuid4().hex[:8]}"
        assignment_id = create_assignment(assignment_name, course_id)
        
        file_size = os.path.getsize(zip_file_path)
        
        # Upload autograder
        upload_start = time.time()
        upload_autograder(assignment_id, zip_file_path, timeout="30")
        upload_end = time.time()
        
        end_time = time.time()
        duration = end_time - start_time
        upload_duration = upload_end - upload_start
        
        # Calculate upload speed
        upload_speed_mbps = (file_size / 1024 / 1024) / upload_duration if upload_duration > 0 else 0
        
        print(f"[Thread-{thread_id}] ✅ Upload {upload_index}: {assignment_name} "
              f"({file_size/1024/1024:.1f}MB in {duration:.2f}s, {upload_speed_mbps:.1f} MB/s)")
        
        return UploadMetrics(
            assignment_id=assignment_id,
            thread_id=thread_id,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success=True,
            file_size=file_size,
            upload_speed_mbps=upload_speed_mbps
        )
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"[Thread-{thread_id}] ❌ Upload {upload_index} failed after {duration:.2f}s: {e}")
        
        return UploadMetrics(
            assignment_id="",
            thread_id=thread_id,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            success=False,
            error=str(e),
            file_size=os.path.getsize(zip_file_path) if os.path.exists(zip_file_path) else 0
        )


def print_detailed_results(metrics: List[UploadMetrics], system_metrics: Dict[str, Any], 
                          test_duration: float):
    """Print comprehensive test results."""
    print("\n" + "="*80)
    print("BULK ASSIGNMENT UPLOAD STRESS TEST RESULTS")
    print("="*80)
    
    successful_uploads = [m for m in metrics if m.success]
    failed_uploads = [m for m in metrics if not m.success]
    
    # Basic statistics
    total_uploads = len(metrics)
    success_count = len(successful_uploads)
    failure_count = len(failed_uploads)
    success_rate = (success_count / total_uploads * 100) if total_uploads > 0 else 0
    
    print(f"OVERALL PERFORMANCE:")
    print(f"  Total uploads attempted: {total_uploads}")
    print(f"  Successful uploads: {success_count} ({success_rate:.1f}%)")
    print(f"  Failed uploads: {failure_count} ({failure_count/total_uploads*100:.1f}%)")
    print(f"  Test duration: {test_duration:.2f}s")
    print()
    
    if successful_uploads:
        # Timing statistics
        durations = [m.duration for m in successful_uploads]
        upload_speeds = [m.upload_speed_mbps for m in successful_uploads]
        file_sizes = [m.file_size / 1024 / 1024 for m in successful_uploads]  # Convert to MB
        
        print(f"TIMING STATISTICS:")
        print(f"  Average upload time: {statistics.mean(durations):.2f}s")
        print(f"  Median upload time: {statistics.median(durations):.2f}s")
        print(f"  Min upload time: {min(durations):.2f}s")
        print(f"  Max upload time: {max(durations):.2f}s")
        print(f"  Std deviation: {statistics.stdev(durations):.2f}s")
        print()
        
        print(f"UPLOAD SPEED STATISTICS:")
        print(f"  Average speed: {statistics.mean(upload_speeds):.2f} MB/s")
        print(f"  Median speed: {statistics.median(upload_speeds):.2f} MB/s")
        print(f"  Min speed: {min(upload_speeds):.2f} MB/s")
        print(f"  Max speed: {max(upload_speeds):.2f} MB/s")
        print()
        
        print(f"FILE SIZE STATISTICS:")
        print(f"  Average file size: {statistics.mean(file_sizes):.1f} MB")
        print(f"  Total data uploaded: {sum(file_sizes):.1f} MB")
        print()
        
        # Throughput analysis
        if test_duration > 0:
            uploads_per_second = success_count / test_duration
            mb_per_second = sum(file_sizes) / test_duration
            print(f"THROUGHPUT:")
            print(f"  Successful uploads per second: {uploads_per_second:.2f}")
            print(f"  Data throughput: {mb_per_second:.2f} MB/s")
            print()
        
        # Concurrency analysis
        thread_performance = {}
        for m in successful_uploads:
            if m.thread_id not in thread_performance:
                thread_performance[m.thread_id] = []
            thread_performance[m.thread_id].append(m.duration)
        
        print(f"THREAD PERFORMANCE:")
        print("-" * 50)
        for thread_id in sorted(thread_performance.keys()):
            durations = thread_performance[thread_id]
            avg_duration = statistics.mean(durations)
            uploads_count = len(durations)
            print(f"  Thread {thread_id:2d}: {uploads_count:2d} uploads, avg {avg_duration:.2f}s")
        print()
    
    # Error analysis
    if failed_uploads:
        print(f"ERROR ANALYSIS:")
        error_counts = {}
        for m in failed_uploads:
            if m.error:
                error_type = m.error.split(':')[0] if ':' in m.error else m.error[:50]
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        print("-" * 50)
        for error_type, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count} occurrences")
        print()
    
    # System resource usage
    if system_metrics:
        print(f"SYSTEM RESOURCE USAGE:")
        print(f"  Peak CPU usage: {system_metrics.get('peak_cpu_percent', 0):.1f}%")
        print(f"  Average CPU usage: {system_metrics.get('avg_cpu_percent', 0):.1f}%")
        print(f"  Peak memory usage: {system_metrics.get('peak_memory_percent', 0):.1f}%")
        print(f"  Peak memory used: {system_metrics.get('peak_memory_used_mb', 0):.1f} MB")
        print(f"  Average memory usage: {system_metrics.get('avg_memory_percent', 0):.1f}%")
        print()
    
    # Performance recommendations
    print(f"PERFORMANCE INSIGHTS:")
    if successful_uploads:
        if success_rate < 95:
            print("  ⚠️  Success rate below 95% - consider investigating server capacity")
        if statistics.mean([m.duration for m in successful_uploads]) > 10:
            print("  ⚠️  High average upload time - check network/server performance")
        if len(set(m.thread_id for m in failed_uploads)) > len(thread_performance) * 0.3:
            print("  ⚠️  Failures distributed across many threads - possible server overload")
    
    print("\n" + "="*80)


def cleanup_assignments(assignment_ids: List[str]):
    """Clean up created assignments."""
    if not assignment_ids:
        return
    
    print(f"\n🧹 Cleaning up {len(assignment_ids)} assignments...")
    deleted_count = 0
    
    for assignment_id in assignment_ids:
        try:
            delete_assignment(assignment_id)
            deleted_count += 1
        except Exception as e:
            print(f"   Failed to delete assignment {assignment_id}: {e}")
    
    print(f"🧹 Cleanup complete. Deleted {deleted_count}/{len(assignment_ids)} assignments.")


def main():
    parser = argparse.ArgumentParser(description="Bulk assignment upload stress test.")
    parser.add_argument("course_id", type=str, help="Valid course ID")
    parser.add_argument("--num_uploads", type=int, default=20,
                       help="Total number of assignment uploads")
    parser.add_argument("--max_workers", type=int, default=8,
                       help="Maximum number of concurrent upload workers")
    parser.add_argument("--zip_size_mb", type=int, default=2,
                       help="Size of test zip files in MB")
    parser.add_argument("--use_custom_zip", type=str, default=None,
                       help="Path to custom zip file to use for uploads")
    parser.add_argument("--cleanup", action="store_true",
                       help="Delete created assignments after test")
    parser.add_argument("--monitor_system", action="store_true",
                       help="Monitor system resources during test")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting bulk assignment upload stress test...")
    print(f"   Course ID: {args.course_id}")
    print(f"   Number of uploads: {args.num_uploads}")
    print(f"   Max concurrent workers: {args.max_workers}")
    print(f"   Zip file size: {args.zip_size_mb} MB")
    print(f"   System monitoring: {'enabled' if args.monitor_system else 'disabled'}")
    
    # Initialize system monitoring
    system_monitor = None
    if args.monitor_system:
        system_monitor = SystemMonitor()
    
    # Prepare zip file
    zip_file_path = None
    cleanup_zip = False
    
    try:
        if args.use_custom_zip and os.path.exists(args.use_custom_zip):
            zip_file_path = args.use_custom_zip
            print(f"📁 Using custom zip file: {zip_file_path}")
        elif os.path.exists(AUTOGRADER_ZIP_PATH):
            zip_file_path = AUTOGRADER_ZIP_PATH
            print(f"📁 Using default autograder zip: {zip_file_path}")
        else:
            print(f"📁 Creating test zip file ({args.zip_size_mb} MB)...")
            zip_file_path = create_test_zip_file(args.zip_size_mb)
            cleanup_zip = True
            print(f"📁 Created test zip: {zip_file_path}")
        
        file_size_mb = os.path.getsize(zip_file_path) / 1024 / 1024
        print(f"📊 File size: {file_size_mb:.1f} MB")
        
        # Start system monitoring
        if system_monitor:
            print("📈 Starting system monitoring...")
            system_monitor.start_monitoring()
        
        # Start the test
        print(f"\n🧪 Starting {args.num_uploads} concurrent uploads...")
        test_start_time = time.time()
        
        # Create upload tasks
        upload_metrics = []
        upload_lock = threading.Lock()
        
        def collect_metrics(future_result):
            with upload_lock:
                upload_metrics.append(future_result)
        
        # Execute uploads with thread pool
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = []
            
            for i in range(args.num_uploads):
                thread_id = i % args.max_workers  # Distribute across workers
                future = executor.submit(upload_assignment_with_metrics, 
                                       thread_id, args.course_id, i, zip_file_path)
                futures.append(future)
            
            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    result = future.result()
                    collect_metrics(result)
                except Exception as e:
                    print(f"Upload task failed with exception: {e}")
                    # Create a failure metric
                    collect_metrics(UploadMetrics(
                        assignment_id="",
                        thread_id=-1,
                        start_time=time.time(),
                        end_time=time.time(),
                        duration=0,
                        success=False,
                        error=str(e)
                    ))
        
        test_end_time = time.time()
        test_duration = test_end_time - test_start_time
        
        # Stop system monitoring
        system_metrics = {}
        if system_monitor:
            system_monitor.stop_monitoring()
            system_metrics = system_monitor.get_peak_metrics()
            print("📈 System monitoring complete.")
        
        # Print results
        print_detailed_results(upload_metrics, system_metrics, test_duration)
        
        # Cleanup if requested
        if args.cleanup:
            successful_assignment_ids = [m.assignment_id for m in upload_metrics 
                                        if m.success and m.assignment_id]
            cleanup_assignments(successful_assignment_ids)
        
        # Cleanup temporary zip file
        if cleanup_zip and zip_file_path:
            try:
                os.unlink(zip_file_path)
                print(f"🗑️  Cleaned up temporary zip file")
            except Exception as e:
                print(f"⚠️  Failed to cleanup temp zip file: {e}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
        # Cleanup on failure
        if args.cleanup and 'upload_metrics' in locals():
            successful_assignment_ids = [m.assignment_id for m in upload_metrics 
                                        if m.success and m.assignment_id]
            cleanup_assignments(successful_assignment_ids)
        
        if cleanup_zip and zip_file_path:
            try:
                os.unlink(zip_file_path)
            except:
                pass
        
        if system_monitor:
            system_monitor.stop_monitoring()


if __name__ == "__main__":
    main()