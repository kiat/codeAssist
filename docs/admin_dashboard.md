# Admin Dashboard Documentation

## Overview

The Admin Dashboard is designed for institution administrators to manage all aspects of the platform, including courses, instructors, and students. Administrators have the highest level of access and can perform actions such as registering instructors (so they do not need to self-enroll), editing or deleting users, and managing courses across all terms.

## Setup

### Create AdminEmail Table
1. Start your Docker containers
```bash
docker compose up
```
2. Run the following commands in a new terminal window to create the AdminEmail table and insert your emails (Replace `your_email@example.com` with the email addresses you want to add.):
```bash
docker exec -it flask_container sh
python admin_emails.py your_email@example.com
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


Admin users log in via Google OAuth2. Upon authentication, the system checks the user's email against a list of pre-approved admin emails stored in the database. Only users with matching email addresses are granted admin privileges.


## Planned Features

- **Instructor Account Enrollment**: remove self-enrollment for instructors; instructor accounts will be created by admins only
- **Login Restrictions**: Allow login only for emails with authorized institution domains
- **Email Verification**: send a verification code to new users for additional validation
