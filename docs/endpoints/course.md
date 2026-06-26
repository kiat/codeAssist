# CodeAssist Course Endpoints

These endpoints are used for retrieving and manipulating course data. This is mostly used for course enrollment actions.

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
