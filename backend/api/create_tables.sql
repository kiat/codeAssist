
/* Create Students table */
CREATE TABLE students (
    id uuid primary key,
    password varchar(60) not null,
    name varchar(30) not null,
    email_address varchar(30) not null UNIQUE,
    sis_user_id varchar(50) not null UNIQUE,
);


CREATE TABLE instructors(
    
)INHERITS (students);

/* Create Courses table */
create table courses (
    id uuid primary key,
    name varchar(50),
    sis_course_id varchar(50),
    semester varchar(50),
    year varchar(50),
    entryCode varchar(50),
    allowEntryCode boolean,
    description varchar(100)
);

/* Create Enrollments table */
create table enrollments (
    student_id uuid not null UNIQUE,
    course_id uuid not null,
    primary key (student_id, course_id),
    foreign key (student_id) references students (id),
    foreign key (course_id) references courses (id)
);

/* Create Assignments table */
create table assignments (
    id uuid primary key,
    name varchar(50) not null,
    course_id uuid not null,
    autograder_file bytea,
    foreign key (course_id) references courses (id)
);

/* Create Submissions table */
create table submissions (
    id uuid primary key,
    student_id uuid not null,
    assignment_id uuid not null,
    student_code_file bytea not null,
    results bytea,
    score float,
    execution_time float,
    executed_at timestamp,
    completed boolean default false,
    foreign key (student_id) references students (id),
    foreign key (assignment_id) references assignments (id)
);

/* Submissions table index */
create index submissions_idx on submissions (student_id, assignment_id);
