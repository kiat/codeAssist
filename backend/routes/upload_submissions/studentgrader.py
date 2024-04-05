import json
import subprocess
import os
import sys

def grade_submission_with_test_cases(submission_script, test_cases_dir):
    results = {'test_cases': []}  # Initialize results dictionary

    # Ensure test_cases_dir exists and contains files
    if not os.path.exists(test_cases_dir) or not os.listdir(test_cases_dir):
        print(f"Test cases directory {test_cases_dir} is empty or does not exist")
        sys.exit(1)

    # List all test case files in the directory
    test_case_files = [f for f in os.listdir(test_cases_dir) if os.path.isfile(os.path.join(test_cases_dir, f))]

    # Iterate through each test case file and run the student submission against it
    for test_case_file in test_case_files:
        test_case_path = os.path.join(test_cases_dir, test_case_file)
        with open(test_case_path, 'r') as tf:
            input_content = tf.read()
            try:
                # Reset file pointer after reading for execution
                tf.seek(0)
                # Run the student submission script with the test case's contents piped into stdin
                proc = subprocess.run(['python3', submission_script], stdin=tf, capture_output=True, text=True, check=True)
                # Store the result, including the input content used
                results['test_cases'].append({
                    'test_case_name': test_case_file, 
                    'input': input_content, 
                    'output': proc.stdout
                })
            except subprocess.CalledProcessError as e:
                # Handle failure, including the input content used and error output, no pass/fail status
                results['test_cases'].append({
                    'test_case_name': test_case_file, 
                    'input': input_content, 
                    'error': e.stderr
                })

    # Serialize results to JSON and save to a file
    with open('/app/results.json', 'w') as f:
        json.dump(results, f, indent=4)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 studentgrader.py <submission_script_path> <test_cases_dir>")
        sys.exit(1)
    
    submission_script_path = sys.argv[1]
    test_cases_dir = sys.argv[2]
    
    grade_submission_with_test_cases(submission_script_path, test_cases_dir)
