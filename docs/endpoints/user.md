# CodeAssist User Endpoints

These endpoints are used to interact with user data, particularly for login procedures.

## POST /create_user

**Accepts JSON data**

**Description:**

<p>Creates a user, which can be a student or instructor based on input, and
generates an id in the database. Currently this route isn't in use and in the
future will be used instead of the create_student and create_instructor routes.</p>

Example input:

    {
      name: "Ricky Woodruff",
      email: "woodruffr@utexas.edu",
      password: "password",
      eid: "rick123",
      role: "0"
    }

Example Output(instructor):

    {
      "email_address":"woodruffr@utexas.edu",
      "id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id": "rick123"
    }

## GET /user_login

**Accepts JSON data**

**Description**

<p>Takes an email and password as input, and returns a 404 if no user is found, and returns all information related to the user.

Example input:

    {
      email: "woodruffr@utexas.edu",
      password: "password",
    }

Example Output:

    {
      "email_address":"woodruffr@utexas.edu",
      "id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id": "rick123"
    }


## GET /get_users

**Accepts Query String**

**Description**

<p>Returns JSON of attributes of a specified user given their email as a query paramter.<p>

Example Input:

      ?email=woodruffr@utexas.edu

Example Output:

    [{
      "email_address":"woodruffr@utexas.edu",
      "id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id": "rick123"
    }, 
    {
      "email_address":"jeffross@utexas.edu",
      "id":"a6984457-048a-44fb-8455-441jdnsk8b9847",
      "name":"Jeff Ross",
      "password":"password",
      "sis_user_id": "at37810"
    }]


## GET /get_user_by_id

**Accepts Query String**

**Description**

<p>Returns JSON of attributes of a user given their id.<p>

Example input:

    
      ?id=6025b3f6-ac5f-4ff9-9357-f5a7fc8a624b
    

Example Output:

    {
      "email_address":"woodruffr@utexas.edu",
      "id":"a6888457-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id": "rick123"
    }

## PUT, POST /update_account

**Accepts JSON data**

**Description:**

<p>Updates account details in the database based on what fields are inputted to
change. Only name and password can be changed for any user.</p>

Example input:

    {
      id:"a9872357-475a-47ab-8455-441cdd8b9744",
      // Optionally include any fields to update
    }

Example Output:

    {
      "email_address":"woodruffr@utexas.edu",
      "id":"a9872357-475a-47ab-8455-441cdd8b9744",
      "name":"Ricky Woodruff",
      "password":"password",
      "sis_user_id": "rick123"
    }
    
---
