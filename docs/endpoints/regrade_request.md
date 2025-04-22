# CodeAssist Regrade Request Endpoints

These endpoints are used for creating and interacting with regrade requests for an assignment submission.

**Accepts Query String**

**Description:**
<p>Gets all latest submissions for an assignments based on course enrollement and assignment </p>

Example Input:
    
      ?course_id=fc8beca8-48b5-41ce-b89c-9b2b31103b72
      assignment_id=dfbd967d-8951-4052-82aa-ce55b1d3d0e7
    

Example Output:
    [
      {
        "email_address": "test2@example.com",
        "executed_at": "Thu, 30 Nov 2023 20:02:55 GMT",
        "score": 90.0,
        "student_name": "test 2"
      },
      {
        "email_address": "tester123@example.com",
        "executed_at": "Thu, 30 Nov 2023 19:48:13 GMT",
        "score": 90.0,
        "student_name": "Test"
      }
    ]

## GET /get_all_assignment_submissions

**Accepts Query String**

**Description**

<p>Returns all the submissions for a given assignment.</p>

Example Input:
    
      ?assignment_id=dfbd967d-8951-4052-82aa-ce55b1d3d0e7
    
  
Example Output:
    [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "file_name": "assignment1_solution.py",
        "submission_number": 3,
        "submitted_at": "2025-02-27T17:30:45",
        "student_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
        "assignment_id": "98765432-abcd-efgh-ijkl-1234567890ab",
        "score": 92.5,
        "execution_time": 0.87,
        "active": true,
        "completed": true
      },
      {
        "id": "660f9511-f30c-52e5-b827-557766551111",
        "file_name": "assignment1_attempt2.py",
        "submission_number": 2,
        "submitted_at": "2025-02-27T16:45:30",
        "student_id": "b2c3d4e5-f6g7-5b6c-9d0e-0f1a2b3c4d5e",
        "assignment_id": "98765432-abcd-efgh-ijkl-1234567890ab",
        "score": 85.0,
        "execution_time": 1.02,
        "active": false,
        "completed": true
      }
    ]



## DELETE /delete_submission

**Accepts Query String**

**Description**

<p>Deletes a submission from the database.</p>

Example Input:

      ?submission_id=176fafed-0a61-41fd-abf9-e055d58b950c
    

Example Output:

    {
      "message": "Submission successfully deleted"
    }



## GET /get_submission_details

**Accepts Query String**

**Description**

<p>Retrieves submission details for a specific submisison given its submission id.</p>

Example Input:

    
      ?submission_id=176fafed-0a61-41fd-abf9-e055d58b950c
    

Example Output:

    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "file_name": "assignment2_solution.py",
      "submission_number": 3,
      "submitted_at": "2025-02-27T17:30:45",
      "student_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
      "assignment_id": "98765432-abcd-efgh-ijkl-1234567890ab",
      "score": 92.5,
      "execution_time": 0.87,
      "active": true,
      "completed": true
    }


## GET /get_active_submission

**Accepts Query String**

**Description**

<p>Gets the active submissions for a student for an assignment given their student id and their assingment id.</p>

Example Input:

    
      ?student_id=a6888457-475a-47ab-8455-441cdd8b9744&
      assignmentId=dfbd967d-8951-4052-82aa-ce55b1d3d0e7
    

Example Output:

    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "file_name": "assignment1_solution.py",
      "submission_number": 2,
      "submitted_at": "2025-02-27T17:15:30",
      "student_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
      "assignment_id": "98765432-abcd-efgh-ijkl-1234567890ab",
      "score": 85.5,
      "execution_time": 1.23,
      "active": true,
      "completed": true
    }

## POST /activate_submission

**Accepts JSON data**

**Description**

<p>Activates a submission and deactivates any currently active submission for the same assignment and student. </p>

Example Input:

    {
      "submission_id": "176fafed-0a61-41fd-abf9-e055d58b950c",
      "student_id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "assignmentId": "dfbd967d-8951-4052-82aa-ce55b1d3d0e7"
    }

Example Output:

    {
      "message": "Submission activated successfully",
      "error": "Error message"
    }


# Regrade Requests

## POST /send_regrade_request

**Accepts JSON data**

**Description:**

<p>Creates a regrade request with the given submission ID and justification.</p>

Example input:

    {
      "submission_id": "176fafed-0a61-41fd-abf9-e055d58b950c",
      "justification": "I believe there was an error in grading."
    }

Example Output:

    {
      "id": "a6888457-475a-47ab-8455-441cdd8b9744",
      "submission_id": "176fafed-0a61-41fd-abf9-e055d58b950c",
      "justification": "I believe there was an error in grading."
    }

## GET /get_regrade_request

**Accepts Query String**

**Description:**

<p>Gets the regrade request associated with a submission ID.</p>

Example input:

    
      ?submission_id=176fafed-0a61-41fd-abf9-e055d58b950c
    

Example Output:

    {
      "submission": { ... },  // Full submission details
      "justification": "I believe there was an error in grading.",
      "reviewed": false
    }
## POST /check_regrade_request

**Accepts JSON data**

**Description:**

<p>Checks if a regrade request exists for the given submission ID.</p>

Example input:

    {
      "submission_id": "176fafed-0a61-41fd-abf9-e055d58b950c"
    }

Example Output:

    {
      "has_request": true
    }

or

    {
      "has_request": false
    }

## POST /delete_regrade_request

**Accepts JSON data**

**Description:**

<p>Deletes the regrade request associated with the given submission ID.</p>

Example input:

    {
      "submission_id": "176fafed-0a61-41fd-abf9-e055d58b950c"
    }

Example Output:

    {
      "message": "Regrade request deleted"
    }

## POST /update_grade

**Accepts JSON data**

**Description:**

<p>Updates the grade of a submission with a new grade.</p>

Example input:

    {
      "submission_id": "176fafed-0a61-41fd-abf9-e055d58b950c",
      "new_grade": 95.0
    }

Example Output:

    {
      "message": "Grade updated successfully"
    }

## GET /get_student_regrade_requests

**Accepts Query String**

**Description:**

<p>Gets all regrade requests for a specific student based on their student ID.</p>

Example input:

    
      ?student_id=a6888457-475a-47ab-8455-441cdd8b9744
    

Example Output:

    [
      {
        "regradeRequestId": "a6888457-475a-47ab-8455-441cdd8b9744",
        "assignmentName": "Assignment 1",
        "studentName": "John Doe",
        "justification": "I believe there was an error in grading.",
        "assignmentId": "dfbd967d-8951-4052-82aa-ce55b1d3d0e7",
        "studentId": "a6888457-475a-47ab-8455-441cdd8b9744",
        "reviewed": false
      }
    ]

## GET /get_instructor_regrade_requests

**Accepts Query String**

**Description:**

<p>Gets all regrade requests for all assignments for an instructor.</p>

Example Input:

    ?course_id=a6888457-475a-47ab-8455-441cdd8b9744


Example Output:

    [
      {
        "assignmentName": "Assignment 1",
        "studentName": "John Doe",
        "justification": "I believe there was an error in grading.",
        "assignmentId": "dfbd967d-8951-4052-82aa-ce55b1d3d0e7",
        "studentId": "a6888457-475a-47ab-8455-441cdd8b9744",
        "reviewed": false
      }
    ]

## POST /set_reviewed

**Accepts JSON data**

**Description:**

<p>Marks a regrade request as reviewed.</p>

Example input:

    {
      "submission_id": "176fafed-0a61-41fd-abf9-e055d58b950c"
    }

Example Output:

    {
      "message": "Review updated successfully"
    }


---
