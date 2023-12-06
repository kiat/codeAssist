# Code Assist

README.md by [Allen Wu](mailto:allen.wu@utexas.edu)

## Quickstart: Local Development

### Requirements:

- python ([Install](https://www.python.org/downloads/))
- postgresql ([Install](https://www.postgresql.org/download/))
- npm ([Install](https://nodejs.org/en/download))

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
6. Create the required tables
    ```bash
    python3 ./backend/init_db.py
    ```
7. Start the backend service  
    Within the backend folder run:
    ```bash
    python3 app.py
    ```
8. Start the frontend service  
    In a NEW terminal  
    cd into the frontend folder and run:
    ```bash
    npm run start
    ```
9. Test end to end functionality by creating a new instructor

### Important ports:
Frontend is hosted at `localhost:3000`  
Backend is hosted at `localhost:5000`  
Server is hosted at `localhost:5432`

## Important Links (Development)

-   [Design Doc](https://www.dropbox.com/scl/fi/ddxu41wbo558d3m7c8t7t/CodeAssist-Design-Doc.paper?dl=0&rlkey=mlyww3cy74tr2utmmdbnsu6eb)
-   [Documentation and Issue Tracking](https://codeassist.atlassian.net/)
