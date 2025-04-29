# Course, Assignment, and Submission Backend Design Doc

## 1. Overview
This backend supports a course management system where instructors can create courses, post assignments, and manage student submissions with automated grading via Docker containers. It uses Flask for the API, SQLAlchemy for ORM, and Docker to sandbox autograders.

## 2. Architecture Overview
```
+------------------+         +-------------------+        +------------------------+
|  course.py       |         |  assignment.py    |        |   submission.py        |
|------------------|         |-------------------|        |------------------------|
| Course creation  | <-----> | Assignment CRUD   | <----> | Submission processing  |
| Enrollment       |         | Extensions, Dupes |        | Docker, AI Feedback    |
+------------------+         +-------------------+        +------------------------+
```

## 3. Modules Summary

### course.py
- **Create / Update / Delete** courses
- **Enroll students**, individually or via CSV
- **Fetch course details, enrollments, and assignments**
- **Store encrypted OpenAI API keys**

### assignment.py
- **Create / Update / Delete / Duplicate** assignments
- **Manage extensions** for individual students
- **Safeguards** to avoid duplicate names in the same course

### submission.py
- **Upload assignments** (autograder zip + setup/run scripts)
- **Build Docker images** for each assignment
- **Upload student submissions**, auto-run against grader inside Docker
- **Track active submission**, store score + execution time
- **Run async AI feedback generation**
- **Support submission switching (activate/deactivate)**

## 4. Key Components

| Component           | Purpose                                               |
|---------------------|--------------------------------------------------------|
| Blueprint           | Separate concerns across files (Flask modular routing) |
| SQLAlchemy Models   | Handle persistent data                                 |
| Schemas             | Cleanly serialize/deserialize data to/from JSON        |
| Docker              | Run autograders in isolated environments               |
| AI Feedback Thread  | Asynchronous grading feedback                          |
| Error Handlers      | Unified exceptions for cleaner code                    |

## 5. Key Design Decisions
- **Dockerized Grading**: Sandboxes untrusted student code, ensuring security.
- **Asynchronous AI Feedback**: Non-blocking user flow, returns results later.
- **One Active Submission** per student-assignment: Ensures clarity in grading state.
- **UUIDs for IDs**: Consistent, secure unique identifiers across entities.
- **CSV Enrollment**: Allows batch onboarding of students.

## 6. Sample Flow: Uploading & Grading
1. Instructor uploads autograder zip → stored + Docker container created
2. Student uploads submission:
   - File copied to Docker
   - `run_autograder` script executed
   - Results parsed and stored in DB
   - AI feedback thread launched
3. Instructor or student fetches results via `/get_results` or `/get_active_submission`
