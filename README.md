# Code Assist

## How to install

1. Clone the repository

    ```bash
    git clone git@github.com:kiat/codeAssist.git
    ```

2. Install Dependencies

    - `python` ([Install](https://www.python.org/downloads/))
    - `docker` ([Install](https://docs.docker.com/get-docker/))
    - `postgresql` ([Install](https://www.postgresql.org/download/))
    - `pip3 install -r ./backend/requirements.txt`
    - `docker-compose`

        ```bash
        pip install docker-compose
        ```

3. Create database  
   After you have successfully installed postgres, use it to create the database that you will use for this project.

4. Create a `.env` file in the backend directory and add your DB connection string

    ```bash
    touch ./backend/.env
    ```

    In your `.env` file, add your connection string:

    ```bash
    DB_CONNECTION_STRING="postgresql://{username}:{password}@localhost:5432/{database}"
    ```

5. Create the required tables
    ```bash
    python3 ./backend/init_db.py
    ```
6. Start the backend service

    ```bash
    docker-compose up backend
    ```

7. Start the frontend service

    ```bash
    docker-compose up frontend
    ```

## Done!

Your backend should now be running on `http://localhost:5000` and your frontend on `http://localhost:3000`.

---

## Contributors

-   Ricky Woodruff

## Important Links (Development)

-   [Design Doc](https://www.dropbox.com/scl/fi/ddxu41wbo558d3m7c8t7t/CodeAssist-Design-Doc.paper?dl=0&rlkey=mlyww3cy74tr2utmmdbnsu6eb)
-   [Documentation and Issue Tracking](https://codeassist.atlassian.net/)
