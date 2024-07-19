/* Create Students table */
CREATE TABLE people (
    id uuid PRIMARY KEY,
    password varchar(60) NOT NULL,
    name varchar(30) NOT NULL,
    email_address varchar(30) NOT NULL UNIQUE,
    sis_user_id varchar(50) NOT NULL UNIQUE,
    role varchar(30) NOT NULL
);

/* Create Courses table */
CREATE TABLE courses (
    id uuid PRIMARY KEY,
    name varchar(50),
    instructor_id uuid NOT NULL,
    sis_course_id varchar(50),
    semester varchar(50),
    year varchar(50),
    entryCode varchar(50),
    allowEntryCode boolean DEFAULT FALSE,
    description varchar(100),
    FOREIGN KEY (instructor_id) REFERENCES people (id)
);

/* Create Enrollments table */
CREATE TABLE enrollments (
    student_id uuid NOT NULL,
    course_id uuid NOT NULL,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES people (id),
    FOREIGN KEY (course_id) REFERENCES courses (id)
);

/* Create Assignments table */
CREATE TABLE assignments (
    id uuid PRIMARY KEY,
    name varchar(50) NOT NULL,
    course_id uuid NOT NULL,
    due_date timestamp,
    anonymous_grading boolean DEFAULT FALSE,
    enable_group boolean DEFAULT FALSE,
    group_size integer,
    leaderboard integer,
    late_submission boolean DEFAULT FALSE,
    late_due_date timestamp,
    manual_grading boolean DEFAULT FALSE,
    autograder_points float,
    published boolean DEFAULT FALSE,
    published_date timestamp,
    autograder_file bytea,
    FOREIGN KEY (course_id) REFERENCES courses (id)
);

/* Create Submissions table */
CREATE TABLE submissions (
    id uuid PRIMARY KEY,
    student_id uuid NOT NULL,
    assignment_id uuid NOT NULL,
    student_code_file bytea NOT NULL,
    results bytea,
    score float,
    execution_time float,
    submitted_at timestamp,
    completed boolean DEFAULT FALSE,
    FOREIGN KEY (student_id) REFERENCES people (id),
    FOREIGN KEY (assignment_id) REFERENCES assignments (id)
);

CREATE TABLE submission_submitters (
    submission_id uuid NOT NULL,
    submitter_id uuid NOT NULL,
    PRIMARY KEY (submission_id, submitter_id),
    FOREIGN KEY (submission_id) REFERENCES submissions (id),
    FOREIGN KEY (submitter_id) REFERENCES people (id)
);

/* Create TestCases table */
CREATE TABLE test_cases (
    id uuid PRIMARY KEY,
    assignment_id uuid NOT NULL,
    test_case_name varchar(255) NOT NULL,
    expected_output text NOT NULL,
    FOREIGN KEY (assignment_id) REFERENCES assignments (id)
);

/* Update TestCaseResults table to include reference to TestCases */
CREATE TABLE test_case_results (
    id uuid PRIMARY KEY,
    submission_id uuid NOT NULL,
    test_case_id uuid NOT NULL,
    student_output text,
    passed boolean,
    FOREIGN KEY (submission_id) REFERENCES submissions (id),
    FOREIGN KEY (test_case_id) REFERENCES test_cases (id)
);

CREATE TABLE regrade_requests (
    id uuid PRIMARY KEY,
    submission_id uuid NOT NULL,
    justification text NOT NULL,
    reviewed boolean DEFAULT FALSE,
    FOREIGN KEY (submission_id) REFERENCES submissions (id)
);



/* Submissions table index */
CREATE INDEX submissions_idx ON submissions (student_id, assignment_id);


- Create a new submission type for assignments that allows professors to have more freedom for manual grading
