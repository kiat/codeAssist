# Admin Dashboard Documentation (WIP)

## Overview

The Admin Dashboard is designed for institution administrators to manage all aspects of the platform, including courses, instructors, and students. Administrators have the highest level of access and can perform actions such as registering instructors (so they do not need to self-enroll), editing or deleting users, and managing courses across all terms.

## Authentication

### OAuth2 Login
Admin users log in via Google OAuth2. Upon authentication, the system checks the user's email against a list of pre-approved admin emails stored in the database. Only users with matching email addresses are granted admin privileges.

### Inserting Admin Users into the Database
With OAuth2 authentication, admin accounts must be explicitly added to the database ahead of time. This step ensures that only approved users can gain admin access upon their first login.

**Todo**
- Insert emails of developer team for them to gain access.

**Method**
- Run a Python script or use database management tools to insert admin emails and roles into the `Admin` table.


## API Routes

- `GET /get_all_courses`: Retrieve all courses in the institution.
- `GET /get_all_instructors`: Retrieve all instructor accounts.
- `GET /get_all_students`: Retrieve all student accounts.

(Additional endpoints for editing, deleting, and creating users/courses are planned or in progress.)

## Frontend Pages & Components

### 1. `AdminSidebar.js`
- Navigation includes:
  - **Courses**: View and manage all courses.
  - **Students**: View, search, and manage all students.
  - **Instructors**: View, search, manage, and register instructors.

### 2. `admin/dashboard`
- The main dashboard page for administrators.
- Displays institutional data, including number of courses, students, and instructors.

### 3. `admin/courses` (In Progress)
- Lists all courses, grouped by term.
- Admins can edit course details, similar to instructor access.

### 4. `admin/students` (In Progress)
- Searchable list of all students (by EID or name).
- Admins can edit or delete student accounts.

### 5. `admin/instructors` (In Progress)
- Searchable list of all instructors (by EID or name).
- Admins can edit or delete instructor accounts.
- Admins can register new instructors directly (no self-enrollment required).


## Planned Features

- **Course Management**: Edit, delete, and create courses with full instructor-level access.
- **Student Management**: Search, edit, and delete student accounts.
- **Instructor Management**: Search, edit, delete, and register instructors.
- **Data Tables**: Filter, sort, and export data for courses, staff, and students.
- **OAuth2 Integration**: Ensure all admin logins use Google OAuth2 for security.
