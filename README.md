# Code Assist

## Quickstart: Local Development

### Important ports:
Frontend is hosted at `localhost:3000`  
Backend is hosted at `localhost:5001`  
Server is hosted at `localhost:5432`


Note: For macOS make sure to turn off Airplay as it uses localport:5000 as well (or just switch to `localhost:5001`)

### Requirements:

- `python` ([Install](https://www.python.org/downloads/))
- `docker` ([Install](https://docs.docker.com/get-docker/))
- npm ([Install](https://nodejs.org/en/download))
- `postgresql` ([Install](https://www.postgresql.org/download/)) (Hold off on downloading this into your system until seeing the steps below)
- `pip3 install -r ./backend/requirements.txt`
- `docker-compose`

    ```bash
    pip3 install docker-compose
    ```

### Setup:

1. Clone the repository (below is https)
    ```bash
    git clone https://github.com/kiat/codeAssist.git
    ```
2. Run the following:
    ```bash
    pip3 install -r ./backend/requirements.txt
    ```
    ```bash
    cd frontend; npm install; cd ..
    ```
3. Create a `.env` file in the frontend directory (don't forget to take out the curly braces)
    ```bash
    touch ./frontend/.env
    ```
    In your `.env` file, add this React environment variable:

    ```bash
    REACT_APP_API_URL={where your backend is hosted}
    ```

4. run `docker compose up`

5. Visit the pgadmin website via the url in the container. login with the default login:  
    `user: admin@admin.com`  
    `password: 12345`

6. In the pgadmin website, register a new server, name it whatever you want. The important information is the connections tab:  
    `Host name/address: host.docker.internal`  
    `Username: root`  
    `Password: root`  

7. In this newly created server, create a new database. Name it `codeassist`. This is important for init_db.py

8. Now in your `flask` container console, run `python3 init_db.py`. This should generate your tables in the codeassist database. You can check that it is populated in the pgadmin website. (under codeassist/Schemas/public/Tables)

9. Create a `.env` file in the backend directory and add your DB connection string

    ```bash
    touch ./backend/.env
    ```

    In your `.env` file, add your connection string:

    ```bash
    DB_CONNECTION_STRING="postgresql://postgres:postgres@host.docker.internal:5432/codeassist"
    ```

10. Start the frontend service -- will automatically open the webpage
    In a NEW terminal  
    cd into the frontend folder and run:
    ```bash
    cd frontend
    ```

    ```bash
    npm start 
    ```

11. If you can access the website and can create a user, you can now begin development :bowtie:


Notes: 
- Make sure Postgres is not running on your system (otherwise you will get errors launching the postgres container because the port will conflict). You can either uninstall postgres completely from your system or just kill the run
- Once again, if you are on macOS, make sure to turn off Airplay because it also runs on `localhost:5000`, otherwise Flask won't run!


## Using [Hoppscotch](https://docs.hoppscotch.io/documentation/getting-started/introduction)
Hoppscotch is open source [Postman](https://www.linkedin.com/advice/1/why-should-you-use-postman-api-testing-skills-software-testing-a6hbe), it can test endpoints pretty well
1. Navigate to [Hoppscotch](https://hoppscotch.io/)
2. Import the collections and environments located in the backend folder. They are named accordingly
3. Make sure that the database is running (whether you're running the backend in docker container or not), otherwise Hoppscotch won't be able to send requests 
4. When creating or updating endpoints, make sure to update the collections as well by [adding/updating that endpoint](https://docs.hoppscotch.io/documentation/getting-started/rest/organizing-requests#adding-requests-to-a-collection). 


Notes:
- Make sure that when you are running the collection that the environment is loaded for the specific request you are running.
- You won't be able to make GET requests until you actually create (POST requests) that student/course/instructor/etc. 
- GET and DELETE requests require you to fill in the fields in the parameter tab, POST requests require you to fill stuff out in the body tab


## Important Links (Development)
-   [Design Doc](https://www.dropbox.com/scl/fi/ddxu41wbo558d3m7c8t7t/CodeAssist-Design-Doc.paper?dl=0&rlkey=mlyww3cy74tr2utmmdbnsu6eb)
-   [Documentation and Issue Tracking](https://codeassist.atlassian.net/)
