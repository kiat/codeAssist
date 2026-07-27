# CodeAssist Submission Endpoints

These endpoints are used during the assignment submission flow. See ~/docs/assignment dir for more info on
specific stages within this flow (autograder, submission, feedback generation).

# Submission

## GET /get_submissions

**Accepts Query String**

**Description:**

<p>Gets all submissions by a student for an assignment and returns it in an array.</p>

Example Input:

    
      ?student_id=a6888457-475a-47ab-8455-441cdd8b9744&
      assignment_id=dfbd967d-8951-4052-82aa-ce55b1d3d0e7
    

Example Output:

    [
      {
        "id": "176fafed-0a61-41fd-abf9-e055d58b950c",
        "student_id":"a6888457-475a-47ab-8455-441cdd8b9744",
        "assignment_id: "dfbd967d-8951-4052-82aa-ce55b1d3d0e7",
        "student_code_file": [binary data],
        "results": [binary data],
        "score": "90",
        "execution_time": "11.015512943267822",
        "submitted_at": "2023-08-09 04:39:27",
        "submission_number": 1,
        "active": "true"
        "completed": "true"
      }
    ]

## GET /get_latest_submission

**Accepts Query String**

**Description:**

<p>Gets the latest submission by a student for an assignment based on the time it was executed at.</p>

Example Input:

    
      ?student_id=a6888457-475a-47ab-8455-441cdd8b9744&
      assignment_id: "dfbd967d-8951-4052-82aa-ce55b1d3d0e7
    

Example Output:

    {
      "id": "176fafed-0a61-41fd-abf9-e055d58b950c",
      "student_id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "assignment_id: "dfbd967d-8951-4052-82aa-ce55b1d3d0e7",
      "student_code_file": [binary data],
      "results": [binary data],
      "score": "90",
      "execution_time": "11.015512943267822",
      "executed_at": "2023-08-09 04:39:27",
      "completed": "true"
    }

## POST /upload_submission

**Accepts JSON data and a file**

**Description:**

<p>Uploads a submission by a student for an assignment into the database. A id for the submission is generated.</p>

Example Input:

    {
      "assignment": [file],
      "student_id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "assignment_id: "dfbd967d-8951-4052-82aa-ce55b1d3d0e7"
    }

Example Output:

    {
      "id": "176fafed-0a61-41fd-abf9-e055d58b950c",
      "student_id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "assignment_id: "dfbd967d-8951-4052-82aa-ce55b1d3d0e7",
      "student_code_file": [binary data],
      "results": [binary data],
      "score": "90",
      "execution_time": "11.015512943267822",
      "executed_at": "2023-08-09 04:39:27",
      "completed": "true"
    }

## POST /upload_assignment_autograder

**Accepts JSON data and a file**

**Description:**

<p>Uploads an autograder for an assignment into the database. It is saved as one of the parts of the assignment it is for in the database.</p>

Example Input:

    {
      "file": [file],
      "assignment_id: "dfbd967d-8951-4052-82aa-ce55b1d3d0e7"
    }

Example Output:

    {
      "autograder_file": [file],
      "autograder_points": "100",
      "course_id":"e575f3bc-bda6-4b14-a1aa-b93717425c59",
      "due_date":"2022-12-17",
      "id":"dfbd967d-8951-4052-82aa-ce55b1d3d0e7",
      "name":"A1",
      "published": false
    }

# GET /get_results
**Accepts Query String**

**Description:**

<p>Gets the results of the latest submission by a student for an assignment for instructor use.</p>

Example Input:

    
      ?email=tester123@example.com&
      assignment_id=dfbd967d-8951-4052-82aa-ce55b1d3d0e7
    

Example Output:

    {
      "id": "176fafed-0a61-41fd-abf9-e055d58b950c",
      "student_id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "assignment_id: "dfbd967d-8951-4052-82aa-ce55b1d3d0e7",
      "student_code_file": [binary data],
      "results": [binary data],
      "score": "90",
      "execution_time": "11.015512943267822",
      "executed_at": "2023-08-09 04:39:27",
      "completed": "true"
    }



# GET /get_course_assignment_latest_submissions

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

---
