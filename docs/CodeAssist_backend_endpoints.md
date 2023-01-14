# CodeAssist backend endpoints

# Student
## POST /create_student

**Accepts JSON data**

Example input:

    {
      name: "Ricky Woodruff",
      email: "woodruffr@utexas.edu",
      password: "password",
    }

Example Output:

    {
      "email_address":"woodruffr@utexas.edu",
      "id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id":null
    }


## POST /student_login

**Accepts JSON data**

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
      "sis_user_id":null
    }



# Instructor
## POST /create_instructor

**Accepts JSON data**

Example input:

    {
      name: "Ricky Woodruff",
      email: "woodruffr@utexas.edu",
      password: "password",
    }

Example Output:

    {
      "email_address":"woodruffr@utexas.edu",
      "id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id":null
    }


## POST /instructor_login

**Accepts JSON data**

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
      "sis_user_id":null
    }



# Course
## POST /create_course

**Accepts JSON data**

Example input:

    {
      "name": "CS371L iOS Mobile Development",
      "instructor_id":"2398ef4a-6c1c-42be-8309-d77f3f7d75f8"
    }

Example output:

    {
      "id":"fc8beca8-48b5-41ce-b89c-9b2b31103b72",
      "instructor_id":"2398ef4a-6c1c-42be-8309-d77f3f7d75f8",
      "name":"CS371L iOS Mobile Development",
      "sis_course_id":null
    }



# Assignment
## POST /create_assignment

**Accepts JSON data**

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



## GET /get_assignment

**Accepts Query String**

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

Example input:

    "student_id=a6888457-475a-47ab-8455-441cdd8b9744"

Example output:

    [
      {
        "course_id":"fc8beca8-48b5-41ce-b89c-9b2b31103b72",
        "student_id":"a6888457-475a-47ab-8455-441cdd8b9744"
      }
    ]



# Other
## GET /get_course_assignments

**Accepts Query String**

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



