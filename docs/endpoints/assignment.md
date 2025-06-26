# CodeAssist Assignment Endpoints

These endpoints are used for creating and interacting with assignments within a course.

# Assignment

## POST /create_assignment

**Accepts JSON data**

**Description:**

<p>Creates an assignment for the course and generates an assignment id for it in the database</p>

Example input:

    {
      "name":"Assignment 1",
      "course_id":"CS101"
    }

Example output:

    {
      "autograder_file": null,
      "course_id":"CS101",
      "id":"dfbd967d-8951-4052-82aa-ce55b1d3d0e7",
      "name":"Assignment 1",
      "published": false,
      "due_date": null,
      "autograder_points": null
    }

## POST, PUT /update_assignment

**Accepts JSON data**

**Description:**

<p>Updates an assignment in the database based on the fields inputted to update</p>

Example input:

    {
      "assignment_id":"dfbd967d-8951-4052-82aa-ce55b1d3d0e7",
      // Optionally include any fields to update
      "name": "Assignment 1.1",
      "published": true,
      "due_date": "12/07/2022",
      "autograder_points": 55.0
    }

Example output:

    {
      "autograder_file":null,
      "course_id":"fc8beca8-48b5-41ce-b89c-9b2b31103b72",
      "id":"dfbd967d-8951-4052-82aa-ce55b1d3d0e7",
      "name": "Assignment 1.1",
      "published": true,
      "due_date": "12/07/2022",
      "autograder_points": 55.0
    }

## POST /duplicate_assignment

**Accepts JSON data**

**Description**

<p>Duplicates a pre-existing assignment with a new name.</p>

Example Input:

    {
      "oldAssignmentId": "550e8400-e29b-41d4-a716-446655440000",
      "newAssignmentTitle": "Duplicate of Assignment 1"
    }

Example Output:

    {
      "id": "660f9511-f30c-52e5-b827-557766551111",
      "name": "Duplicate of Assignment 1",
      "course_id": "98765432-abcd-efgh-ijkl-1234567890ab",
      "due_date": "2025-03-15T23:59:59",
      "anonymous_grading": false,
      "enable_group": false,
      "group_size": null,
      "leaderboard": null,
      "late_submission": true,
      "late_due_date": "2025-03-20T23:59:59",
      "manual_grading": false,
      "autograder_points": 100.0,
      "published": false,
      "published_date": null,
      "container_id": "docker-container-123",
      "autograder_timeout": 300
    }



## DELETE /delete_assignment

**Accepts Query String**

**Description:**

<p>Deletes the assignment from the database.</p>

Example Input:

    
      ?assignment_id=dfbd967d-8951-4052-82aa-ce55b1d3d0e7
    

Example Output:

    {
      Assignment deleted successfully
    }

## GET /get_assignment

**Accepts Query String**

**Description:**

<p>Gets the assignment from the database and returns it</p>

Example input:
    
        ?assignment_id=dfbd967d-8951-4052-82aa-ce55b1d3d0e7
    

Example output:

    {
      "autograder_file": null,
      "autograder_points": null,
      "course_id":"e575f3bc-bda6-4b14-a1aa-b93717425c59",
      "due_date":"2022-12-17",
      "id":"dabe443b-b8b1-403a-92b6-003cfd0f4eb2",
      "name":"A1",
      "published": false
    }

## POST /create_extension

**Accepts JSON Data**

**Description**

<p>Extends an assignment for a specific student.</p>

Example Input:
    {
      "assignment_id": "550e8400-e29b-41d4-a716-446655440000",
      "student_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
      "release_date_extension": "2025-03-01T00:00:00",
      "due_date_extension": "2025-03-20T23:59:59",
      "late_due_date_extension": "2025-03-25T23:59:59"
    }


Example Output:
    {
      "id": "770a0622-g41d-63f6-c938-668877662222",
      "assignment_id": "550e8400-e29b-41d4-a716-446655440000",
      "student_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
      "release_date_extension": "2025-03-01T00:00:00",
      "due_date_extension": "2025-03-20T23:59:59",
      "late_due_date_extension": "2025-03-25T23:59:59"
    }

## GET /get_extension

**Accepts Query String**

**Description**

<p>Returns the extension for a student for a particular assingment.</p>

Example Input:
    
      ?assignment_id=550e8400-e29b-41d4-a716-446655440000&
      student_id=a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d
    

Example Output:

    {
      "id": "770a0622-g41d-63f6-c938-668877662222",
      "assignment_id": "550e8400-e29b-41d4-a716-446655440000",
      "student_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
      "release_date_extension": "2025-03-01T00:00:00",
      "due_date_extension": "2025-03-20T23:59:59",
      "late_due_date_extension": "2025-03-25T23:59:59"
    }


## GET /get_assignment_extensions

**Accepts Query String**

**Description**

<p>Returns the list of extension for an assignment.</p>

Example Input:
    
      ?assignment_id=770a0622-g41d-63f6-c938-668877662222
    


Example Output:
    [
      {
        "id": "770a0622-g41d-63f6-c938-668877662222",
        "assignment_id": "550e8400-e29b-41d4-a716-446655440000",
        "student_id": "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d",
        "release_date_extension": "2025-03-01T00:00:00",
        "due_date_extension": "2025-03-20T23:59:59",
        "late_due_date_extension": "2025-03-25T23:59:59"
      },
      {
        "id": "880b1733-h52e-74g7-d049-779988773333",
        "assignment_id": "550e8400-e29b-41d4-a716-446655440000",
        "student_id": "b2c3d4e5-f6g7-5b6c-9d0e-0f1a2b3c4d5e",
        "release_date_extension": "2025-03-02T00:00:00",
        "due_date_extension": "2025-03-22T23:59:59",
        "late_due_date_extension": "2025-03-27T23:59:59"
      }
    ]

## DELETE /delete_extension

**Accepts Query String**

**Description**

<p>Deletes an extension from an assignment.</p>

Example Input:

Example Input:
    
      ?extension_id=770a0622-g41d-63f6-c938-668877662222
    

Example Output:
    {
      "message": "Extension deleted successfully!"
    }

---
