# CodeAssist Design Doc
Adaptive AI‑Powered Feedback and Grading for Programming Education
## Motivation
Efficient, high‑quality feedback is critical in programming courses. Traditional manual grading is time‑intensive for instructors and slow for students who need rapid guidance. Auto‑graders (e.g., Gradescope) help—but they frequently provide static, task‑specific feedback that does not foster transferable problem‑solving strategies or metacognitive skills.
CodeAssist aims to bridge this gap by delivering personalized, adaptive, and rapid feedback on debugging, efficiency, style, and design patterns—all while scaling to courses with hundreds of simultaneous submissions.

## Key Features
* **AI‑Powered Feedback** – Line‑level suggestions on correctness, optimization, documentation, and style generated via a configurable Large Language Model (LLM).
* **Adaptive Learning Loop** – Tracks each student’s recurring mistakes and feeds context into future prompts to encourage metacognitive growth.
* **Autograder Integration** – Instructors can upload custom autograders to be executed in secure Docker containers.
* **Real‑Time Results** – Students receive grades and AI feedback seconds after submission.
* **Role‑Specific Dashboards** – Intuitive React interfaces for instructors (course / assignment management) and students (grades, submissions, feedback).
* **Open Source & Self‑Hosted** – Simple Docker Compose deployment so individual instructors or entire universities can run CodeAssist on‑premises or in the cloud.

## Summary
CodeAssist is a free and open-source feedback system designed for programming courses. It can be used in computer science courses to provide automated and rapid feedback on students' programming assignment submissions. CodeAssist offers feedback on various aspects of students' code, including debugging, efficiency, style, and object-oriented design patterns, in various formats. While offering students static feedback on their code, as current systems do, proves helpful in addressing specific coding problems within particular tasks, it might fall short of enabling students to develop transferable strategies for other coding challenges. 

Thus, our study focuses on the following research questions:
  1. How can an adaptive AI-assisted feedback system support students’ development of metacognition?
  2. How can AI-assisted feedback systems support the reinforcement of students’ metacognition?
  3. How AI-assisted feedback systems should generate personalized feedback for CS education?

## System Architecture
### High‑Level Overview
| Layer | Technology | Responsibilities |
|-------|------------|------------------|
| **Frontend** | React | Authentication, dashboards, submission UI |
| **Backend** | Flask | REST APIs, auth |
| **Database** | PostgreSQL | Courses, users, submissions, feedback |
| **Sandbox** | Docker | Autograder & AI execution |


To start, we will offer some basic functionality for both instructors and students:

**Instructors**

- Create courses and assignments
- Upload an autograder to automatically grade student submissions
- Enroll registered students in their course

**Students**

- View their registered courses and associated assignments
- Receive their assignment grade immediately after submission 


We plan to make CodeAssist simple to install so that universities or even university professors can easily install our software. 

## System Design

The system’s design leverages a modular approach: a frontend plugin that captures student code submissions, a processing pipeline that analyzes syntax and semantics, and a backend service exposing REST endpoints for feedback retrieval. These API endpoints handle authentication, submission uploads, compilation checks, and retrieval of recommended improvements or error messages. Once the code is processed, a feedback report is generated and sent back to the user interface. This end-to-end flow is orchestrated by a microservices architecture, promoting easier maintenance and scalability across different programming languages.

![6b321f1d87f6d4ec75be66a1978ea9f6](https://github.com/user-attachments/assets/a255db27-5e43-4564-a10e-b9854b8b945c)


# Frontend

Our ReactJS frontend provides similar functionality to Gradescope. When users first load the page, they are presented with the option to sign up or login as either a student or instructor.


![CodeAssist landing page](https://paper-attachments.dropboxusercontent.com/s_09C2C6457685AED4FCCA9A0FADFF67EF8DD44ED32ADBC94D9A4DCA550765B697_1670562775822_Screenshot+2022-12-09+at+12.12.49+AM.png)



## Instructor Dashboard View

After a successful login or register action, instructors will be redirected to their dashboard where they can see their existing courses and create new ones. For each course, instructors will be able to add students (using their CodeAssist-registered email), create assignments, and view each student’s submission history for all assignments.

![8bdf5a397cd021dc58d2641c4f2f6eba](https://github.com/user-attachments/assets/08463e93-779e-430b-8fc9-0837ef25a32d)


## Student Dashboard View

The student view is very similar to the instructor view with the caveat that the student’s dashboard will be empty until an instructor adds them to their course. Students will be able to view their courses, assignments, and grades all within the CodeAssist dashboard. They can also submit their solutions to assignments and receive immediate feedback.


![268a41728cd4ad1e2126d17538c6a244](https://github.com/user-attachments/assets/29ad9886-1bc2-4b28-b53c-20fb3ccee5b2)

## Tailored AI Feedback:
![2cd266287f2db66222ca6c09471dd3ba](https://github.com/user-attachments/assets/224c4163-06ad-46ab-89e5-7e9c0ff9726a)



# Backend

Our Python/Flask backend provides a suite of REST API endpoints to the frontend. It is also connected to our PostgreSQL database, so it can efficiently read and write all necessary data that is needed to maintain user state. The full list of endpoints is provided in the linked document below. 

[+CodeAssist backend endpoints](https://paper.dropbox.com/doc/CodeAssist-backend-endpoints-9UwD0povL54nNneIA6PNz) 

The CodeAssist backend takes advantage of Docker to ensure that all student code is executed in a sandboxed environment. This ensures that we protect against malicious code or code with unintended consequences. When a student submits code for their assignment, we save the file to the database, copy the file and the assignment autograder into a new docker image, execute the docker image in a container, and finally, store the result in our database and return it to the frontend. 



# Data Model
## SQL Database Model 

After exploring SQL and NoSQL options for our database, I recommended we use a SQL Database model. A NoSQL database, specifically a document model, won’t provide us with any advantages given that we won’t be loading a single document at once. Additionally, we have several many-to-many relationships, which makes using a document database difficult. In order to make our queries, we’ll likely need to filter on `student_id = {current_student_id}`. To speed up these queries, we can add indices (single or complex) to large tables to make our queries faster. Finally, SQL databases allow us to maintain data accuracy with `cascade delete`. If we delete a row in a parent table, related rows in child tables will also be deleted. NoSQL databases don’t have this feature, and this would add additional work on our end to ensure data correctness every time a row is deleted. 

**Student Table**

| id            | uuid (primary key) |
| ------------- | ------------------ |
| password      | varchar            |
| name          | varchar            |
| email_address | varchar            |
| sis_user_id   | varchar            |

**Instructor Table**

| id            | uuid (primary key) |
| ------------- | ------------------ |
| password      | varchar            |
| name          | varchar            |
| email_address | varchar            |
| sis_user_id   | varchar            |


**Enrollment Table (composite primary key)**

| student_id | Student Foreign Key (primary key) |
| ---------- | --------------------------------- |
| course     | Course Foreign Key (primary key)  |

**Course Table**

| id              | uuid (primary key)            |
| --------------- | ----------------------------- |
| name            | varchar                       |
| instructor_id   | Instructor Foreign Key (uuid) |
| sis_course_id   | varchar                       |
| semester        | varchar                       |
| year            | varchar                       |
| entryCode       | varchar                       |
| allowEntryCode  | boolean                       |
| description     | varchar                       |

**Assignment Table**

| id                | uuid (primary key) |
| ----------------- | ------------------ |
| name              | varchar            |
| course_id         | Course Foreign Key |
| due_date          | date               |
| anonymous_grading | boolean            |
| enable_group      | boolean            |
| group_size        | int                |
| leaderboard       | int                |
| late_submission   | boolean            |
| late_due_date     | date               |
| manual_grading    | boolean            |
| autograder_points | float              |
| published         | boolean            |
| published_date    | date               |
| autograder_file   | bytea              |


**Submission Table (composite index)**

| id                | uuid (primary key)               |
| ----------------- | -------------------------------- |
| student_id        | Student Foreign Key (index)      |
| assignment_id     | Assignment Foreign Key (index 2) |
| student_code_file | bytea                            |
| results           | bytea                            |
| score             | float (percentage 0.0-100.0)     |
| execution_time    | float (ms) # less than 60        |
| executed_at       | date                             |
| completed         | boolean ( default false )        |



## UML Diagram

![](https://paper-attachments.dropboxusercontent.com/s_09C2C6457685AED4FCCA9A0FADFF67EF8DD44ED32ADBC94D9A4DCA550765B697_1670559611334_CodeAssist_UML.png)


----------
# Future Work
[ ] Add session authentication (using cookies)
[ ] Look into potential web security vulnerabilities (XSS, CSRF, etc)
[ ] Hash passwords in our database (use MD5?)
[ ] Add TA roles
[ ] Kubernetes to horizontally scale web and backend servers
[ ] Integrate with Canvas
[ ] Add caching layer
[ ] Use ML to learn about common student mistakes and how they solve them + use this information to help suggest fixes for future students

# Important Links

[CodeAssist Github Repository](https://github.com/kiat/codeAssist)

