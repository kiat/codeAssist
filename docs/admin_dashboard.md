# Admin Dashboard Documentation

## Overview

The Admin Dashboard is designed for institution administrators to manage all aspects of the platform, including courses, instructors, and students. Administrators have the highest level of access and can perform actions such as registering instructors (so they do not need to self-enroll), editing or deleting users, and managing courses across all terms.

## Setup

### Create AdminEmail Table
1. Add your email address to `admin_emails.py` inside the `emails` list:
```
emails = [
    # Add more emails as needed
]
```
2. Run the following commands in the terminal to create the AdminEmail table and insert your emails:
```
docker exec -it flask_container sh
python admin_emails.py
```

### Setup `frontend/.env`
For development purposes, you can directly use the following Client ID in your `frontend/.env` file: 
```
REACT_APP_CLIENT_ID=1039210497435-6hckku1vojl8ii7su5m1bhj0h1msligr.apps.googleusercontent.com
```

**To Create a New OAuth Client ID (skip if using the provided ID)**
1. Create a new project at https://console.cloud.google.com/welcome/new
2. Click Oauth Consent Screen and make the app External
3. Put your project name and emails for User Support Email and Developer Contact Information and click next
4. In the Data Access tab, add the following scopes: ./auth/userinfo.email, auth/userinfo.profile, openid
5. In the Audience tab, add your own email/developer emails for the test users section
6. In the Clients tab, create an Oauth 2.0 Client ID for a web application (For the URLs make it the frontend host, e.g. http://localhost:3000 and http://localhost)
7. Save the newly created Client ID in the frontend .env file as REACT_APP_CLIENT_ID

**Example `.env`**
```
REACT_APP_API_URL=http://localhost:5001
REACT_APP_CLIENT_ID=1039210497435-6hckku1vojl8ii7su5m1bhj0h1msligr.apps.googleusercontent.com
```

### Google Login
1. On the login page, click "Google Sign In"
2. Select the email address you previously added to `AdminEmails`
3. If the login is successful and the email is recognized, you will be redirected to the Admin Dashboard

## Authentication

### OAuth2 Login
Admin users log in via Google OAuth2. Upon authentication, the system checks the user's email against a list of pre-approved admin emails stored in the database. Only users with matching email addresses are granted admin privileges.



## API Routes

- `GET /get_all_courses`: Retrieve all courses in the institution.
- `GET /get_all_instructors`: Retrieve all instructor accounts.
- `GET /get_all_students`: Retrieve all student accounts.
- `POST /admin_update_account`: Allow admins to update the name, EID, or email of an existing instructor or student account.

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
- Searchable list of all courses (by CourseID, name, year, semester, or instructor name).
- Admins can edit course details, similar to instructor access.

### 4. `admin/students` (In Progress)
- Searchable list of all students (by EID or name).
- Admins can edit or delete student accounts.
- Display courses each student is enrolled in.

### 5. `admin/instructors` (In Progress)
- Searchable list of all instructors (by EID or name).
- Admins can edit or delete instructor accounts.
- Admins can register new instructors directly (no self-enrollment required).
- Display Courses each instructor teaches.


## Planned Features

- **Course Management**: Edit, delete, and create courses with full instructor-level access.
- **Student Management**: Search, edit, and delete student accounts.
- **Instructor Management**: Search, edit, delete, and register instructors.
- **Data Tables**: Filter, sort, and export data for courses, staff, and students.
