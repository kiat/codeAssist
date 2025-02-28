# CodeAssist backend endpoints

# User

## POST /create_user

**Accepts JSON data**

**Description:**

<p>Creates a user, which can be a student or instructor based on input, and
generates an id in the database. Currently this route isn't in use and in the
future will be used instead of the create_student and create_instructor routes.</p>

Example input:

    {
      name: "Ricky Woodruff",
      email: "woodruffr@utexas.edu",
      password: "password",
      eid: "rick123",
      role: "0"
    }

Example Output(instructor):

    {
      "email_address":"woodruffr@utexas.edu",
      "id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id": "rick123"
    }

## GET /user_login

**Accepts JSON data**

**Description**

<p>Takes an email and password as input, and returns a 404 if no user is found, and returns all information related to the user.

Example input:

    {
      email: "woodruffr@utexas.edu",
      password: "password",
    }

Example Output:

    {
      "email_address":"woodruffr@utexas.edu",
      "id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id": "rick123"
    }


## GET /get_users

**Accepts Query String**

**Description**

<p>Returns JSON of attributes of a specified user given their email as a query paramter.<p>

Example Input:

      ?email=woodruffr@utexas.edu

Example Output:

    [{
      "email_address":"woodruffr@utexas.edu",
      "id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id": "rick123"
    }, 
    {
      "email_address":"jeffross@utexas.edu",
      "id":"a6984457-048a-44fb-8455-441jdnsk8b9847",
      "name":"Jeff Ross",
      "password":"password",
      "sis_user_id": "at37810"
    }]


## GET /get_user_by_id

**Accepts Query String**

**Description**

<p>Returns JSON of attributes of a user given their id.<p>

Example input:

    
      ?id=6025b3f6-ac5f-4ff9-9357-f5a7fc8a624b
    

Example Output:

    {
      "email_address":"woodruffr@utexas.edu",
      "id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id": "rick123"
    }

## PUT, POST /update_account

**Accepts JSON data**

**Description:**

<p>Updates account details in the database based on what fields are inputted to
change. Only name and password can be changed for any user.</p>

Example input:

    {
      id:"a9872357-475a-47ab-8455-441cdd8b9744",
      // Optionally include any fields to update
    }

Example Output:

    {
      "email_address":"woodruffr@utexas.edu",
      "id":"a9872357-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id": "rick123"
    }


---

# Course

## POST /create_course

**Accepts JSON data**

**Description:**

<p>Creates a course in the database based on the data input and creates an id 
for the course</p>

Example input:

    {
      "name": "CS371L iOS Mobile Development",
      "instructor_id":"2398ef4a-6c1c-42be-8309-d77f3f7d75f8",
      "semester" : "Spring",
      "year" : "2024",
      "entryCode": "ABC123"
    }

Example output:

    {
      "id":"fc8beca8-48b5-41ce-b89c-9b2b31103b72",
      "name":"CS371L iOS Mobile Development",
      "sis_course_id":null,
      "semester" : "Spring",
      "year" : "2024",
      "entryCode": "ABC123"
    }

## POST /enroll_course

**Accepts JSON data**

**Description:**

<p>Enrolls a student in a course using entry code. This is used on the student 
side where they can enroll into a course without a instructor adding them
if they have the entry code.</p>

Example input:

    {
      student_id : "a6888457-475a-47ab-8455-441cdd8b9744",
      entryCode: "ABC123"
    }

Example Output(enrollment):

    {
      "student_id": "a6888457-475a-47ab-8455-441cdd8b9744",
      "course_id": "fc8beca8-48b5-41ce-b89c-9b2b31103b72"
    }

## POST /update_course

**Accepts JSON data**

**Description:**

<p>Updates a course in the database based on the fields inputted to be updated.</p>

Example input:

    {
      "course_id": "fc8beca8-48b5-41ce-b89c-9b2b31103b72"
      // Optionally include any fields to update
    }

Example Output:

    {
      "id":"fc8beca8-48b5-41ce-b89c-9b2b31103b72",
      "instructor_id":"2398ef4a-6c1c-42be-8309-d77f3f7d75f8",
      "name":"CS371L iOS Mobile Development",
      "sis_course_id":null,
      "semester" : "Spring",
      "year" : "2024",
      "entryCode": "ABC123"
    }

## DELETE /delete_course

**Accepts Query String**

**Description:**

<p>Deletes a course from the database</p>

Example input:

    
      ?course_id=fc8beca8-48b5-41ce-b89c-9b2b31103b72
    

## DELETE /delete_all_assignments

**Accepts Query String**

**Description:**

<p>Deletes all assignment from the database given a course ID.</p>

Example input:

    
      ?course_id=fc8beca8-48b5-41ce-b89c-9b2b31103b72
    

---

# Enrollment

## POST /create_enrollment

**Accepts JSON data**

**Description:**

<p>Enrolls a student in a course by creating an enrollment in the database. 
Enrollments in the database hold a student id and the matched id of the course
they were enrolled into.</p>

Example input:

    {
      "student_id": "a6888457-475a-47ab-8455-441cdd8b9744",
      "course_id":"fc8beca8-48b5-41ce-b89c-9b2b31103b72"
    }

Example output:

    {
      "course_id":"fc8beca8-48b5-41ce-b89c-9b2b31103b72",
      "student_id":"a6888457-475a-47ab-8455-441cdd8b9744"
    }

## POST /update_role

**Accepts JSON data**

**Description**

<p>Updates the role of a user.<p>

Example input:

    {
      "student_id": "ai38018",
      "course_id": "840810"
      "new_role": 1
    }

Example output:

    {
      "message": "Role update successfully"
    }
    {
      "error": "Enrollment not found:
    }

## POST /create_enrollment_bulk

**Accepts JSON data**

**Description:**

<p>Mass enrolls multiple students in a course at once and creates enrollments in
 the database for all of them.</p>

Example input:

    {
      "course_id":"e575f3bc-bda6-4b14-a1aa-b93717425c59",
      "student_ids": [
        "177e9a44-8135-4b23-a99b-ad94e9694948",
        "e5d5d204-f44f-4397-86a0-93ab49a5f817",
        "70750539-1bce-400d-a5ee-2a580a96c0bd"
      ]
    }

Example output:

    {
      "message": "Success"
    } // Check HTTP 200 response


## POST /create_enrollment_csv

**Accepts Request File**

**Description**

Mass enrolls students using a csv file as input.

Example Input:

    File: "CS101-students.csv

Example Output:

    {
      "success": true,
      "enrolled_count": 3,
      "course_id": "550e8400-e29b-41d4-a716-446655440000",
      "enrolled_students": [
        {
          "student_id": "123456789",
          "status": "enrolled"
        },
        {
          "student_id": "987654321",
          "status": "enrolled"
        },
        {
          "student_id": "456789123",
          "status": "enrolled"
        }
      ],
      "message": "Successfully enrolled 3 students in the course."
    }

## GET /get_user_enrollments

**Accepts Query String**

**Description:**

<p>Gets all enrollments for a single student from the enrollments in the database.</p>

Example input:

    "student_id=a6888457-475a-47ab-8455-441cdd8b9744"

Example output:

    [
      {
        "course_id":"fc8beca8-48b5-41ce-b89c-9b2b31103b72",
        "student_id":"a6888457-475a-47ab-8455-441cdd8b9744"
      }
    ]

## GET /get_course_enrollment

**Accepts Query String**

**Description:**

<p>Gets all students enrolled in a specific course and returns it in an array.</p>

Example input:

"course_id":"e575f3bc-bda6-4b14-a1aa-b93717425c59"

Example output:

    [
      {
        "email_address":"student@student.com",
        "name":"Student 1"
      },
      {
        "email_address":"student2@student.com",
        "name":"Student 2"
      },
      {
        "email_address":"student3@student.com",
        "name":"Student 3"
      }
    ]

## GET /get_course_assignments

**Accepts Query String**

**Description:**

<p>Gets all of the assignments for a course and returns them to the user in an array.</p>

Example input:

"course_id"="fc8beca8-48b5-41ce-b89c-9b2b31103b72"

Example output:

    [
      {
        "autograder_file":null,
        "course_id":"fc8beca8-48b5-41ce-b89c-9b2b31103b72",
        "id":"dfbd967d-8951-4052-82aa-ce55b1d3d0e7",
        "name":"Assignment 1"
      }
    ]

## GET /get_course_info

**Accepts Query String**

**Description:**

<p>Gets the information about the course stored in the database and returns it 
to the user.</p>

Example Input:

    {
      "course_id": "fc8beca8-48b5-41ce-b89c-9b2b31103b72"
    }

Example Output:

    {
      "id":"fc8beca8-48b5-41ce-b89c-9b2b31103b72",
      "name":"CS371L iOS Mobile Development",
      "sis_course_id":null,
      "semester" : "Spring",
      "year" : "2024",
      "entryCode": "ABC123"
    }

## GET /get_student_enrollment

**Accepts Query String**

**Description**

<p>Returns list of all students registered to a course given the course's unique id.</p>

Example Input:
    {
      "course_id": "fc8beca8-48b5-41ce-b89c-9b2b31103b72"
    }

Example Output:

    [{
      "email_address":"woodruffr@utexas.edu",
      "id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id": "rick123"
    }, 
    {
      "email_address":"jeffross@utexas.edu",
      "id":"a6984457-048a-44fb-8455-441jdnsk8b9847",
      "name":"Jeff Ross",
      "password":"password",
      "sis_user_id": "at37810"
    }]


---


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

    {
      "assignment_id=dfbd967d-8951-4052-82aa-ce55b1d3d0e7"
    }

Example Output:

    {
      Assignment deleted successfully
    }

## GET /get_assignment

**Accepts Query String**

**Description:**

<p>Gets the assignment from the database and returns it</p>

Example input:
    {
        "assignment_id=dfbd967d-8951-4052-82aa-ce55b1d3d0e7"
    }

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
    {
      assignment_id: "550e8400-e29b-41d4-a716-446655440000",
      student_id: "a1b2c3d4-e5f6-4a5b-8c7d-9e0f1a2b3c4d"
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


## GET /get_assignment_extensions

**Accepts Query String**

**Description**

<p>Returns the list of extension for an assignment.</p>

Example Input:
    {
      "assignment_id": "770a0622-g41d-63f6-c938-668877662222"
    }


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
    {
      "extension_id": "770a0622-g41d-63f6-c938-668877662222"
    }

Example Output:
    {
      "message": "Extension deleted successfully!"
    }

# Submissions

## GET /get_submissions

**Accepts Query String**

**Description:**

<p>Gets all submissions by a student for an assignment and returns it in an array.</p>

Example Input:

    {
      "student_id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "assignment_id: "dfbd967d-8951-4052-82aa-ce55b1d3d0e7"
    }

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

    {
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

    {
      "email":"tester123@example.com",
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



# GET /get_course_assignment_latest_submissions

**Accepts Query String**

**Description:**
<p>Gets all latest submissions for an assignments based on course enrollement and assignment </p>

Example Input:
    {
      "course_id"="fc8beca8-48b5-41ce-b89c-9b2b31103b72"
      "assignment_id"="dfbd967d-8951-4052-82aa-ce55b1d3d0e7"
    }

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
    {
      "assignment_id"="dfbd967d-8951-4052-82aa-ce55b1d3d0e7"
    }
  
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

    {
      "submission_id": "176fafed-0a61-41fd-abf9-e055d58b950c"
    }

Example Output:

    {
      "message": "Submission successfully deleted"
    }



## GET /get_submission_details

**Accepts Query String**

**Description**

<p>Retrieves submission details for a specific submisison given its submission id.</p>

Example Input:

    {
      "submission_id": "176fafed-0a61-41fd-abf9-e055d58b950c"
    }

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

    {
      "student_id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "assignmentId": "dfbd967d-8951-4052-82aa-ce55b1d3d0e7"
    }

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

    {
      "submission_id": "176fafed-0a61-41fd-abf9-e055d58b950c"
    }

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

    {
      "student_id": "a6888457-475a-47ab-8455-441cdd8b9744"
    }

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

# Old Endpoints Documentation

# Student

## POST /create_student

**Accepts JSON data**

**Description:**

<p>Creates a student and generates an id in the database</p>

Example input:

    {
      name: "Ricky Woodruff",
      email: "woodruffr@utexas.edu",
      password: "password",
      eid: "rick123"
    }

Example Output:

    {
      "email_address":"woodruffr@utexas.edu",
      "id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id": "rick123"
    }

## POST /student_login

**Accepts JSON data**

**Description:**

<p>Logs in a student that exists in the database into their account</p>

Example input:

    {
      email: "woodruffr@utexas.edu",
      password: "password",
    }

Example Output:

    {
      "email_address":"woodruffr@utexas.edu",
      "id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id": "rick123"
    }

## GET /get_student

**Accepts Query String**

**Description:**

<p>Gets the student from the database based on the email put in</p>

Example input:

    {
      email: "woodruffr@utexas.edu",
    }

Example Output:

    {
      "email_address":"woodruffr@utexas.edu",
      "id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id": "rick123"
    }

### GET /get_student_by_id

**Accepts Query String**

**Description:**

<p>Gets the student from the database based on the student ID provided.</p>

**Example Input:**

    {
      "id": "a6888457-475a-47ab-8455-441cdd8b9744"
    }

**Example Output:**

    {
      "email_address": "woodruffr@utexas.edu",
      "id": "a6888457-475a-47ab-8455-441cdd8b9744",
      "name": "Ricky Woodruff",
      "sis_user_id": "rick123"
    }

# Instructor

## POST /create_instructor

**Accepts JSON data**

**Description:**

<p>Creates an instructor and generates an id in the database</p>

Example input:

    {
      name: "Ricky Woodruff",
      email: "woodruffr@utexas.edu",
      password: "password",
      eid: "rick123"
    }

Example Output:

    {
      "email_address":"woodruffr@utexas.edu",
      "id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id": "rick123"
    }

### GET /get_instructor_by_id

**Accepts Query String**

**Description:**

<p>Gets the instructor from the database based on the instructor ID provided.</p>

**Example Input:**

    {
      "id": "2398ef4a-6c1c-42be-8309-d77f3f7d75f8"
    }

**Example Output:**

    {
      "email_address": "woodruffr@utexas.edu",
      "id": "2398ef4a-6c1c-42be-8309-d77f3f7d75f8",
      "name": "Ricky Woodruff",
      "sis_user_id": "rick123"
    }


## GET /get_instructor_courses

**Accepts Query String**

**Description:**

<p>Gets all the courses created by a certain instructor and returns it in an array</p>

Example input:
    {
      "instructor_id":"2398ef4a-6c1c-42be-8309-d77f3f7d75f8"
    }

Example output:

    [
      {
        "id":"a6b6b84e-5b4b-480b-8b75-5066e0c96d66",
        "instructor_id":"2398ef4a-6c1c-42be-8309-d77f3f7d75f8",
        "name":"CS371L Mobile Computing",
        "sis_course_id":null
      }
    ]