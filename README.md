# Code Assist

## Quickstart: Local Development

### Requirements:

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
   DB_CONNECTION_STRING="postgresql://{username}:{password}@host.docker.internal:5432/codeassist"
```


8. Start the backend service using  docker-compose

    ```bash
    docker-compose up backend
    ```

8. Start the frontend service
    In a NEW terminal  
    cd into the frontend folder and run:
    ```bash
    cd frontned
    ```

    ```bash

    npm start 
    ```

9. Test end to end functionality by creating a new instructor

### Important ports:
Frontend is hosted at `localhost:3000`  
Backend is hosted at `localhost:5000`  
Server is hosted at `localhost:5432`

## Important Links (Development)

-   [Design Doc](https://www.dropbox.com/scl/fi/ddxu41wbo558d3m7c8t7t/CodeAssist-Design-Doc.paper?dl=0&rlkey=mlyww3cy74tr2utmmdbnsu6eb)
-   [Documentation and Issue Tracking](https://codeassist.atlassian.net/)
