import sys
import subprocess
import os
import json

def run_tests(solution_script, test_files_dir):
    results = {'test_cases': []}  # Initialize results dictionary

    # List all test files in the directory
    test_files = [f for f in os.listdir(test_files_dir) if os.path.isfile(os.path.join(test_files_dir, f))]

    # Iterate through each test file and run the solution script against it
    for test_file in test_files:
        test_file_path = os.path.join(test_files_dir, test_file)
        with open(test_file_path, 'r') as tf:
            input_content = tf.read()
            try:
                # Reset file pointer after reading
                tf.seek(0)
                # Run the solution script with the test file's contents piped into stdin
                proc = subprocess.run(['python3', solution_script], stdin=tf, capture_output=True, text=True, check=True)
                # Store the result including input content
                results['test_cases'].append({
                    'test_case_name': test_file, 
                    'input': input_content,  # Include input content
                    'output': proc.stdout
                })
            except subprocess.CalledProcessError as e:
                # Handle failure but only store the test case name and error output, no pass/fail status
                results['test_cases'].append({'test_case_name': test_file, 'input': input_content, 'output': e.stderr})

    # Serialize results to JSON and save to a file
    results_file = os.path.join('results.json')
    with open(results_file, 'w') as rf:
        json.dump(results, rf, indent=4)

        
    with open(results_file, 'r') as rf:
        print(rf.read())

if __name__ == "__main__":
    # Ensure two arguments are passed: the solution script path and the test files directory
    if len(sys.argv) != 3:
        print("Usage: python3 autograder.py <solution_script> <test_files_dir>")
        sys.exit(1)
    
    solution_script = sys.argv[1]
    test_files_dir = sys.argv[2]
    
    run_tests(solution_script, test_files_dir)
