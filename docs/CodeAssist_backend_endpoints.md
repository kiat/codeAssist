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

## POST /update_account

**Accepts JSON data**

**Description:**

<p>Updates account details in the database based on what fields are inputted to
change</p>

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

## POST /instructor_login

**Accepts JSON data**

**Description:**

<p>Logs in an instructor that exists in the database to their account</p>

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

    {
      "course_id": "fc8beca8-48b5-41ce-b89c-9b2b31103b72"
    }

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

# Assignment

## POST /create_assignment

**Accepts JSON data**

**Description:**

<p>Creates an assignment for the course and generates an assignment id for it in the database</p>

Example input:

    {
      "name":"Assignment 1",
      "course_id":"fc8beca8-48b5-41ce-b89c-9b2b31103b72"
    }

Example output:

    {
      "autograder_file": null,
      "course_id":"fc8beca8-48b5-41ce-b89c-9b2b31103b72",
      "id":"dfbd967d-8951-4052-82aa-ce55b1d3d0e7",
      "name":"Assignment 1",
      "published": false,
      "due_date": null,
      "autograder_points": null
    }

## POST /update_assignment

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

    "assignment_id=dfbd967d-8951-4052-82aa-ce55b1d3d0e7"

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

## GET /get_student_enrollments

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

    {
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
    }

## GET /get_latest_submission

**Accepts Query String**

**Description:**

<p>Gets the latest submission by a student for an assignment based on the time 
it was executed at.</p>

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

<p>Uploads a submission by a student for an assignment into the database. A id 
for the submission is generated.</p>

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

<p>Uploads an autograder for an assignment into the database. It is saved as one 
of the parts of the assignment it is for in the database.</p>

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

<p>Gets the results of the latest submission by a student for an assignment for
instructor use.</p>

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


# Other

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

## GET /get_instructor_courses

**Accepts Query String**

**Description:**

<p>Gets all the courses created by a certain instructor and returns it in an array</p>

Example input:

    "instructor_id":"2398ef4a-6c1c-42be-8309-d77f3f7d75f8"

Example output:

    [
      {
        "id":"a6b6b84e-5b4b-480b-8b75-5066e0c96d66",
        "instructor_id":"2398ef4a-6c1c-42be-8309-d77f3f7d75f8",
        "name":"CS371L Mobile Computing",
        "sis_course_id":null
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
