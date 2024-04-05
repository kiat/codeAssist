#!/bin/bash

echo "Hello from Entrypoint.sh"

# Assuming ${FILENAME} contains the name of the student's submission script
# and assuming test cases are located in /app/test_cases directory
echo "Running student grader script with test cases"
python /app/studentgrader.py "/app/${FILENAME}" "/app/test_cases"

# Optionally, print out the contents of the results file for debugging purposes
echo "Contents of /app/results.json:"
cat /app/results.json


ls -aR /app
