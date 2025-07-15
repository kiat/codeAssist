# Code Assist

## Quickstart: Linux Local Development

### Important ports:
Frontend is hosted at `localhost:3000`  
Backend is hosted at `localhost:5001`  

### Notes: 
Ensured that backend container is run as a non-root user, with no admin 
capabilities, and no way to increase the amount of privileges that it has
Removed access to editing filesystem, instead created a temp folder for things like 
logging 
Removed the port for postgres (no longer exposed)
Created a network that all the containers can communicate with each other on 
For production deployment, do not locally host the backend 



### Requirements:

- `python` ([Install](https://www.python.org/downloads/))
- `docker` ([Install](https://docs.docker.com/get-docker/))
- npm ([Install](https://nodejs.org/en/download))
- `postgresql` ([Install](https://www.postgresql.org/download/)) (Hold off on downloading this into your system until seeing the steps below)

### Setup:

1. Clone the repository (below is https)
    ```bash
    git clone https://github.com/kiat/codeAssist.git
    ```

2. Create a venv in the backend and activate it then run make install to install backend and frontend dependencies:    
    ```
    cd backend 
    python3.12 -m venv venv
    source venv/bin/activate 
    cd ..
    make install
    ```
3. Create a `.env` file in the frontend directory (don't forget to take out the curly braces)
    ```bash
    touch ./frontend/.env
    ```
    In your `.env` file, add this React environment variable:

    ```
    REACT_APP_API_URL=http://localhost:5001
    ```

4. run `docker compose up` and then give user permissions to access the volumes with 
'''sudo chown -R 1000:1000 ./backend
sudo chmod -R u+rwx ./backend'''


5. Visit the pgadmin website via the url in the container. login with the default login:  
    `user: admin@admin.com`  
    `password: 12345`

6. In the pgadmin website, register a new server, name it whatever you want. The important information is the connections tab:  
    `Host name/address: db`  
    `Username: postgres`  
    `Password: postgres`  

7. In this newly created server, create a new database. Name it `codeassist`. This is important for `init_db.py`

8. Now in your `flask` container console, run `python3 init_db.py`. This should generate your tables in the codeassist database. You can check that it is populated in the pgadmin website. (under codeassist/Schemas/public/Tables)

9. Create a `.env` file in the backend directory and add your DB connection string

    ```bash
    touch ./backend/.env
    ```

    In your `.env` file, add your connection string:

    ```bash
    DB_CONNECTION_STRING="postgresql://postgres:postgres@db:5432/codeassist"
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

## Testing
**As of 3/3/2025, only backend tests have started being written.

To run tests, run the the following from root directory:
```
make test
```


## Important Links (Development)
-   [Design Doc](https://www.dropbox.com/scl/fi/ddxu41wbo558d3m7c8t7t/CodeAssist-Design-Doc.paper?dl=0&rlkey=mlyww3cy74tr2utmmdbnsu6eb)
-   [Documentation and Issue Tracking](https://codeassist.atlassian.net/)