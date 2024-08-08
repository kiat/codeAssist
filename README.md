# Code Assist

## Quickstart: Local Development

### Requirements:

Note: for macOS make sure to turn off Airplay as it uses localport:5001 as well

- `python` ([Install](https://www.python.org/downloads/))
- `docker` ([Install](https://docs.docker.com/get-docker/))
- npm ([Install](https://nodejs.org/en/download))
- `postgresql` ([Install](https://www.postgresql.org/download/))
- `pip3 install -r ./backend/requirements.txt`
- `docker-compose`

    ```bash
    pip install docker-compose
    ```

### Setup:

1. Clone the repository
    ```bash
    git clone git@github.com:kiat/codeAssist.git
    ```
2. Run the following:
    ```bash
    pip3 install -r ./backend/requirements.txt
    ```
    ```bash
    cd frontend;npm install; cd ..
    ```
3. Create a `.env` file in the frontend directory
    ```bash
    touch ./frontend/.env
    ```
    In your `.env` file, add this React environment variable:

    ```bash
    REACT_APP_API_URL={where your backend is hosted}
    ```
4. Create the database  
    After you have successfully installed postgres, use it to create the database that you will use for this project.
5. Create a `.env` file in the backend directory and add your DB connection string

    ```bash
    touch ./backend/.env
    ```

    In your `.env` file, add your connection string:

    ```bash
    DB_CONNECTION_STRING="postgresql://{username}:{password}@localhost:5432/{database}"
    ```



    
6. Start Postgres DB and Create the required tables
   
    ```bash
    sudo systemctl start postgresql
    ```
    
    ```bash
    python3 ./backend/init_db.py
    ```
7.  Start Docker and run backend
   


    ```bash
    sudo systemctl start docker

    ```
    (Optional) Enable Docker and Postgres to start on boot

    ```bash
    sudo systemctl enable docker
    ```

If you run backend in a docker container, then the backend inside the container needs to connect to the localhost databases. 
To enable this you need to make the following change in your .env file. 
```
   DB_CONNECTION_STRING="postgresql://root:root@host.docker.internal:5432/codeassist"
```


8. Start the backend service using  docker-compose

    ```bash
    docker-compose up backend
    ```

8. Start the frontend service
    In a NEW terminal  
    cd into the frontend folder and run:
    ```bash
    cd frontend
    ```

    ```bash
    npm start 
    ```

9. Test end to end functionality by creating a new instructor

## New Backend stack completely on docker
Prerequisites:
- Postgres is not currently running on your system (otherwise you will get errors launching the postgres container because the port will conflict). Either uninstall postgres completely from your system or just kill it
- If you are on macOS, make sure to turn off Airplay because it also runs on localport:5001

Steps
1. Install docker with the steps above
2. run `docker compose up`
3. Visit the pgadmin website via the url in the container. login with the default login:  
    `user: admin@admin.com`  
    `password: 12345`
4. In the pgadmin website, register a new server, name it whatever you want. The important information is the connections tab:  
    `Host name/address: host.docker.internal`  
    `Username: root`  
    `Password: root`  
5. In this newly created server, create a new database. Name it `codeassist`. This is important for init_db.py
6. Now in your `flask` container console, run `python3 init_db.py`. This should generate your tables in the codeassist database. You can check that it is populated in the pgadmin website. (under codeassist/Schemas/public/Tables)
7. Begin sending requests.

## Using [Hoppscotch](https://docs.hoppscotch.io/documentation/getting-started/introduction)
Hoppscotch is open source [Postman](https://www.linkedin.com/advice/1/why-should-you-use-postman-api-testing-skills-software-testing-a6hbe), it can test endpoints pretty well
1. Navigate to [Hoppscotch](https://hoppscotch.io/)
2. Import the collections and environments located in the backend folder. They are named accordingly
3. Make sure that the database is running (whether you're running the backend in docker container or not), otherwise Hoppscotch won't be able to send requests 
4. When creating or updating endpoints, make sure to update the collections as well by [adding/updating that endpoint](https://docs.hoppscotch.io/documentation/getting-started/rest/organizing-requests#adding-requests-to-a-collection). 

- Note 1: Make sure that when you are running the collection that the environment is loaded for the specific request you are running.
- Note 2: You won't be able to make GET requests until you actually create (POST requests) that student/course/instructor/etc. 

### Important ports:
Frontend is hosted at `localhost:3000`  
Backend is hosted at `localhost:5001`  
Server is hosted at `localhost:5432`

## Important Links (Development)

-   [Design Doc](https://www.dropbox.com/scl/fi/ddxu41wbo558d3m7c8t7t/CodeAssist-Design-Doc.paper?dl=0&rlkey=mlyww3cy74tr2utmmdbnsu6eb)
-   [Documentation and Issue Tracking](https://codeassist.atlassian.net/)
