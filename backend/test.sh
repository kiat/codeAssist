#!/bin/bash

# Define a log file for potential errors and another for passed tests
error_log="api_errors.log"
pass_log="api_pass.log"

# This function sends a request and checks the response.
# It captures the 'id' from the JSON response silently and logs the status to a file without console output.
function check_response {
    local response=$(mktemp)
    local status=$(bash -c "$1 -o $response -w '%{http_code}'")
    local id=""

    if [ "$status" -ne 200 ]; then
        echo "$2: FAIL" >> $error_log
        cat $response >> $error_log
        echo "$2: FAIL"
    else
        id=$(cat $response | jq -r '.id')
        echo "$2: PASS" >> $pass_log
        echo "$2: PASS"
    fi

    rm $response
    echo $id  # This will be captured by the caller for further use, silently
}

# Store IDs in variables without outputting them
instructor_id=$(check_response "curl -s -X POST -H 'Content-Type: application/json' -d \
'{\"name\": \"Instructor Name\", \"email\": \"instructor@email.com\", \"password\": \"password\", \"eid\": \"unique-instructor-id\"}' \
localhost:5001/create_instructor" "Create Instructor" | tail -n 1)

student_id=$(check_response "curl -s -X POST -H 'Content-Type: application/json' -d \
'{\"name\": \"Ricky Woodruff\", \"email\": \"ricky@student.com\", \"password\": \"password\", \"eid\": \"unique-student-id\"}' \
localhost:5001/create_student" "Create Student" | tail -n 1)

# Perform login tests without outputting IDs
check_response "curl -s -X POST -d '{\"email\":\"instructor@email.com\", \"password\":\"password\"}' \
localhost:5001/instructor_login -H 'Content-Type: application/json'" "Instructor Login" | tail -n 1 > /dev/null

check_response "curl -s -X POST -d '{\"email\":\"ricky@student.com\", \"password\":\"password\"}' \
localhost:5001/student_login -H 'Content-Type: application/json'" "Student Login" | tail -n 1 > /dev/null

# Create a course using the captured instructor ID without outputting the course ID
course_id=$(check_response "curl -s -X POST -H 'Content-Type: application/json' -d \
'{\"name\": \"Introduction to Curl Testing\", \"instructor_id\": \"$instructor_id\", \"semester\": \"Fall\", \"year\": 2024, \"entryCode\": \"1000\"}' \
localhost:5001/create_course" "Create Course" | tail -n 1)

# Enroll in Course
check_response "curl -s -X POST -d '{\"entryCode\":\"1000\", \"student_id\":\"$student_id\"}' localhost:5001/enroll_course -H 'Content-Type: application/json'" "Enroll in Course" | tail -n 1 > /dev/null

# Create Assignment
assignment_id=$(check_response "curl -s -X POST -d '{\"name\":\"A1\", \"course_id\":\"$course_id\"}' localhost:5001/create_assignment -H 'Content-Type: application/json'" "Create Assignment" | tail -n 1)

# Update Assignment
check_response "curl -s -X POST -d '{\"assignment_id\":\"$assignment_id\", \"name\":\"Updated Assignment A1\"}' localhost:5001/update_assignment -H 'Content-Type: application/json'" "Update Assignment" | tail -n 1 > /dev/null

# Get Assignment (using a specific assignment_id from your example)
check_response "curl -s localhost:5001/get_assignment?assignment_id=$assignment_id" "Get Assignment" | tail -n 1 > /dev/null


# # Create Bulk Enrollments

# # Upload Submission

# # Additional Tests for Edge Cases and Error Handling

# # Attempt to create a course with missing parameters

# # Update non-existent assignment

# # Get non-existent assignment

# # Attempt to enroll with wrong entry code

# # Delete Assignment (with dependencies handled)

# # Attempt login with wrong credentials

# # Incorrect method use case

# # Check handling of unsupported methods

# # Output all tests done

