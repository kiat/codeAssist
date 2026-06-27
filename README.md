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

### Setup:

1. Clone the repository (below is https)
    ```bash
    git clone https://github.com/kiat/codeAssist.git
    ```
2. Run the following to install backend and frontend dependencies:    
    ```
    make install
    ```
3. Create a `.env` file in the frontend directory (don't forget to take out the curly braces)
    ```bash
    touch ./frontend/.env
    ```
    In your `.env` file, add this React environment variable:

    ```
    REACT_APP_API_URL={where your backend is hosted}
    ```

4. Create a `.env` file in the backend directory and add your DB connection string

    ```bash
    touch ./backend/.env
    ```

    In your `.env` file, add your connection string:

    ```bash
    DB_CONNECTION_STRING="postgresql://postgres:postgres@host.docker.internal:5432/codeassist"
    PASSWORD_SALT="obtain this value from the main developer or project lead"
    ```
Note: PASSWORD_SALT is used for password hashing so the same password produces consistent hashed values across local environments. The backend can still run without this value, but it may fall back to less secure password handling depending on the local configuration. For normal development and testing, developers should use the shared project salt in their .env file when available.

5. run `docker compose up`

6. Visit the pgadmin website via the url in the container. login with the default login:  
    `user: admin@admin.com`  
    `password: 12345`

7. In the pgadmin website, register a new server, name it whatever you want. The important information is the connections tab:  
    `Host name/address: db` (use `db` if connecting from the pgAdmin container, or `host.docker.internal`/`localhost` if running pgAdmin locally outside Docker)  
    `Username: postgres`  
    `Password: postgres`  

8. In this newly created server, create a new database. Name it `codeassist`. This is important for `init_db.py`

9. Now in your `flask` container console, run `python3 init_db.py`. This should generate your tables in the codeassist database. You can check that it is populated in the pgadmin website. (under codeassist/Schemas/public/Tables)

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

As of 6/27/2026, backend tests have started being written. Some frontend tests are also available and can be run separately.

### Run all tests

From the root directory:

```bash
make test
```

### Run backend tests only

From the root directory:

```bash
cd backend
python -m pytest
```

Or, if you want to skip stress tests:

```bash
cd backend
python -m pytest test --ignore=test/stress
```

### Run frontend tests only

From the root directory:

```bash
cd frontend
npm test
```

To run frontend tests once without watch mode:

```bash
cd frontend
npm test -- --watchAll=false
```

### Database migration note

If you are testing a PR that includes a new database migration, restart the containers and run the Flask database upgrade before testing.

From the root directory:

```bash
docker compose down
docker compose up -d
docker compose exec backend flask db upgrade
```

If the database schema is not updated, new backend fields or tables may not exist locally, and the feature may fail even if the code is correct.


