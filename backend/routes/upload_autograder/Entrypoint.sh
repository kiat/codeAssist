#!/bin/bash

# Read environment variables
ASSIGNMENT_ID=${ASSIGNMENT_ID}
FILENAME=${FILENAME}

echo "ASSIGNMENT_ID: ${ASSIGNMENT_ID}"
echo "FILENAME: ${FILENAME}"
# echo "Contents of /app directory:"
# ls -al /app

# Unzip the uploaded file to /app/solution
unzip "/app/${ASSIGNMENT_ID}/${FILENAME}" -d /app/solution

# Ensure the results directory exists
mkdir -p /app/results

# Dynamically find the Python solution file and the test cases directory
SOLUTION_SCRIPT=$(find /app/solution -type f -name '*.py' | head -n 1)
TEST_FILES_DIR=$(find /app/solution -type d -mindepth 1 -maxdepth 1 | head -n 1)

# Check if the solution script and test cases directory were found
if [ ! -f "${SOLUTION_SCRIPT}" ]; then
    echo "Solution script not found."
    exit 1
fi

if [ ! -d "${TEST_FILES_DIR}" ]; then
    echo "Test cases directory not found."
    exit 1
fi

# Run the Python autograder
if ! python3 /app/autograder.py "${SOLUTION_SCRIPT}" "${TEST_FILES_DIR}"; then
    echo "Autograder script failed."
    exit 1
fi

echo "Contents of /app directory after running scripts:"
ls -R /app/*

# Clean up after running the tests
rm -rf /app/solution /app/${FILENAME}
