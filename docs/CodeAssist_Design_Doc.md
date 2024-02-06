# CodeAssist Design Doc

# Motivation
In any area of education, the ability to efficiently grade assignments and provide meaningful feedback to students is essential. In computer science education specifically, instructors can utilize auto-grading systems like Gradescope to auto-grade their assignments, manage course enrollments and grades, and give meaningful feedback to students. 
CodeAssit is a system that can provide personalized detailed feedback about students' programming assignments including debugging, efficiency, style, and object-oriented design patterns, in various formats. 

# Summary
CodeAssist is a free and open-source feedback system designed for programming courses. It can be used in computer science courses to provide automated and rapid feedback on students' programming assignment submissions. CodeAssist offers feedback on various aspects of students' code, including debugging, efficiency, style, and object-oriented design patterns, in various formats. While offering students static feedback on their code, as current systems do, proves helpful in addressing specific coding problems within particular tasks, it might fall short of enabling students to develop transferable strategies for other coding challenges. 

Thus, our study focuses on the following research questions:
  1. How can an adaptive AI-assisted feedback system support students’ development of metacognition?
  2. How can AI-assisted feedback systems support the reinforcement of students’ metacognition?
  3. How AI-assisted feedback systems should generate personalized feedback for CS education?




To start, we will offer some basic functionality for both instructors and students:

**Instructors**

- Create courses and assignments
- Upload an autograder to automatically grade student submissions
- Enroll registered students in their course

**Students**

- View their registered courses and associated assignments
- Receive their assignment grade immediately after submission 


We plan to make CodeAssist simple to install so that universities or even university professors can easily install our software. 

# System Design

Over the course of the Fall 2022 semester, we designed and built the CodeAssist system. Our system consists of a React frontend, a Python/Flask backend, and a PostgreSQL database. The end-to-end flow for a student submitting an assignment is detailed below.


![Student submission flow](https://paper-attachments.dropboxusercontent.com/s_09C2C6457685AED4FCCA9A0FADFF67EF8DD44ED32ADBC94D9A4DCA550765B697_1670558151174_Blank+diagram.png)



# Frontend

Our ReactJS frontend provides similar functionality to Gradescope. When users first load the page, they are presented with the option to sign up or login as either a student or instructor.


![CodeAssist landing page](https://paper-attachments.dropboxusercontent.com/s_09C2C6457685AED4FCCA9A0FADFF67EF8DD44ED32ADBC94D9A4DCA550765B697_1670562775822_Screenshot+2022-12-09+at+12.12.49+AM.png)



## Instructor View

After a successful login or register action, instructors will be redirected to their dashboard where they can see their existing courses and create new ones. For each course, instructors will be able to add students (using their CodeAssist-registered email), create assignments, and view each student’s submission history for all assignments.


![Instructor home dashboard](https://paper-attachments.dropboxusercontent.com/s_09C2C6457685AED4FCCA9A0FADFF67EF8DD44ED32ADBC94D9A4DCA550765B697_1670562910050_Screenshot+2022-12-09+at+12.15.05+AM.png)



## Student View

The student view is very similar to the instructor view with the caveat that the student’s dashboard will be empty until an instructor adds them to their course. Students will be able to view their courses, assignments, and grades all within the CodeAssist dashboard. They can also submit their solutions to assignments and receive immediate feedback.


![Student home dashboard](https://paper-attachments.dropboxusercontent.com/s_09C2C6457685AED4FCCA9A0FADFF67EF8DD44ED32ADBC94D9A4DCA550765B697_1670563106747_Screenshot+2022-12-09+at+12.18.20+AM.png)



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



# Installation Instructions
## How to install

1. Clone the repository
    `git clone git@github.com:kiat/codeAssist.git`
2. Install Dependencies
    - `python` ([Install](https://www.python.org/downloads/))
    - `docker` ([Install](https://docs.docker.com/get-docker/))
    - `postgresql` ([Install](https://www.postgresql.org/download/))
    - `pip3 install -r ./backend/requirements.txt`
    - `docker-compose`
3. Create database 
4. After you have successfully installed postgres, use it to create the database that you will use for this project.
5. Create a `.env` file in the backend directory and add your DB connection string
    `touch ./backend/.env`
6. In your `.env` file, add your connection string:
    `DB_CONNECTION_STRING="postgresql://{username}:{password}@localhost:5432/{database}"`
7. Start Docker and Postgres
    `sudo systemctl start docker`
    `sudo systemctl start postgresql`
8. (Optional) Enable Docker and Postgres to start on boot
    `sudo systemctl enable docker`
    `sudo systemctl enable postgresql`
9. Create the required tables
    `bash python3 ./backend/init_db.py`
10. Start the backend service
    `docker-compose up backend`
11. Start the frontend service
    `docker-compose up frontend`
## Done!

Your backend should now be running on `http://localhost:5000` and your frontend on `http://localhost:3000`.

----------
# Future Work
[ ] 60s timeout on submissions
[ ] Add session authentication (using cookies)
[ ] Look into potential web security vulnerabilities (XSS, CSRF, etc)
[ ] Hash passwords in our database (use MD5?)
[ ] Add TA roles
[ ] Enable instructors to add manual grading components of assignments
[ ] Kubernetes to horizontally scale web and backend servers
[ ] Integrate with Canvas
[ ] Add caching layer
[ ] Use ML to learn about common student mistakes and how they solve them + use this information to help suggest fixes for future students

# Important Links

[CodeAssist Github Repository](https://github.com/kiat/codeAssist)

