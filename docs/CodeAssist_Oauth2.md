# CodeAssist Google Login/Sign up Doc

Because CodeAssist is a based around UT Austin's programming courses, a necessary function was to add Oauth2 and eventually SSO sign in to allow for quick and easy user registration. Each user has a unique email tied to them through UT Austin's pre-exisiting system, allowing for a secure and fool-proof method for users to access the application.

# Creating a Google Client ID

1. Create a new project at https://console.cloud.google.com/welcome/new
2. Click Oauth Consent Screen and make the app External
3. Put your project name and emails for User Support Email and Developer Contact Information and click next
4. Add the following scopes: ./auth/userinfo.email, auth/userinfo.profile, openid
5. Add your own email/developer emails for the test users section
6. Click Credentials on the side and create an Oauth Client ID for a web application (For the URLs make it the frontend host, e.g. http://localhost:3000 and http://localhost)
7. Save the newly created Client ID in the frontend .env file as REACT_APP_CLIENT_ID

**An Example .env**
    ```
    REACT_APP_API_URL=http://localhost:5000/
    REACT_APP_CLIENT_ID=6385ospaidfpwoiee1sa56678uckg9futpnp7hhdq8a.apps.googleusercontent.com
    ```

# Frontend

The new addition create a sign-on button underneath the original 2 button sign up and log in buttons. Eventually, these 2 sign up and login buttons should disappear and user verification should only be done through Google's Oauth2 service or an UT SSO. Upon clicking sign in, the page should should return an id_token which can be used for verification when submitted to the backend. Then, the application checks whether or not a user is already is present within the system. If so, then sign them in. If not, start the process for creating a new account.

Response Format:
    {
        "clientId": "<YOUR_CLIENT_ID>",
        "credential": "<ID_TOKEN>",
        "select_by": "btn"
    }

# Backend

The backend works similarly to the current user signup and login features in place. First, before any action, it authenticates whether or not the id token is functional. Then it checks whether or not the user already exists within the database. If they do not, then a new user is a created with a random, secure 12 length password. Then the user is logged in afterwards.
