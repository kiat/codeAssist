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
3. Create a `.env` file in the frontend directory.
    ```bash
    touch ./frontend/.env
    ```
    In `frontend/.env`, add the backend URL used by the React app:

    ```bash
    REACT_APP_API_URL=http://localhost:5001
    GENERATE_SOURCEMAP=false
    ```

    `REACT_APP_API_URL` should point at the Flask backend. For normal local Docker development, use `http://localhost:5001`.

4. Create a backend `.env` file from the committed example, then fill in the values.

    ```bash
    cp ./backend/.env.example ./backend/.env
    ```

    On Windows PowerShell, the same copy command is:

    ```powershell
    Copy-Item .\backend\.env.example .\backend\.env
    ```

    The backend example file is `backend/.env.example`. It documents every supported backend environment variable without committing real secrets. A local Docker development `.env` usually starts like this:

    ```bash
    DB_CONNECTION_STRING="postgresql://postgres:postgres@db:5432/codeassist"
    SECRET_KEY="replace-with-random-session-secret"
    API_SECRET_KEY=
    PASSWORD_SALT=
    FRONTEND_ORIGIN="http://localhost:3000"
    ```

    Backend environment variables:

    - `DB_CONNECTION_STRING`: SQLAlchemy/PostgreSQL connection URL. Use `db` as the hostname when the backend runs in Docker Compose with the included Postgres service. If you run Flask directly on your host machine and Postgres is exposed locally, use `localhost` instead.
    - `SECRET_KEY`: Flask session signing secret. Set this to a long random value and never commit it.
    - `API_SECRET_KEY`: Fernet key used to encrypt stored course/assignment AI provider API keys. Keep it stable for the same database, otherwise previously encrypted keys cannot be decrypted.
    - `PASSWORD_SALT`: Salt used for password hashing. For shared dev databases, obtain the shared value from the project lead; for isolated local testing, use a stable dev-only value.
    - `FRONTEND_ORIGIN`: Exact React origin allowed by backend CORS, normally `http://localhost:3000` in local development.

    Do not leave placeholder text in `API_SECRET_KEY` or `PASSWORD_SALT`. To generate both values automatically, leave them blank and run:

    ```bash
    cd backend
    python init_encryption_keys.py
    ```

    Optional backend environment variables for session auth:

    ```bash
    SESSION_COOKIE_SAMESITE="Lax"   # set to "None" if the frontend is on a different domain
    SESSION_COOKIE_SECURE="false"   # must be "true" over HTTPS whenever SameSite is "None"
    ```

5. Optional: configure Gemini over Vertex AI in `backend/.env`.

    CodeAssist supports Gemini through the regular Gemini Developer API and through Google Cloud Vertex AI. Vertex AI credentials are server-level deployment settings, so instructors should not paste Vertex credentials into a course or assignment form.

    For Vertex AI Express / API-key mode:

    ```bash
    VERTEX_AI_AUTH_MODE=api_key
    VERTEX_AI_API_KEY="replace-with-server-managed-vertex-key"
    GOOGLE_CLOUD_LOCATION=global
    ```

    `GOOGLE_CLOUD_PROJECT` is optional in API-key mode. If it is set, CodeAssist passes both project and location to the Vertex client.

    For standard Vertex AI with Application Default Credentials:

    ```bash
    GOOGLE_CLOUD_PROJECT="your-google-cloud-project-id"
    GOOGLE_CLOUD_LOCATION=global
    GOOGLE_APPLICATION_CREDENTIALS="/path/inside/backend/container/service-account.json"
    ```

    Leave `VERTEX_AI_AUTH_MODE` unset for ADC mode. The Google Cloud project must have Vertex AI enabled, and the configured identity or API key needs the `aiplatform.endpoints.predict` permission. More details are in `docs/ai/vertex-setup.md`.

6. Run Docker Compose:

    ```bash
    docker compose up
    ```

7. Visit the pgadmin website via the url in the container. login with the default login:
    `user: admin@admin.com`  
    `password: 12345`

8. In the pgadmin website, register a new server, name it whatever you want. The important information is the connections tab:
    `Host name/address: db` (use `db` if connecting from the pgAdmin container, or `host.docker.internal`/`localhost` if running pgAdmin locally outside Docker)  
    `Username: postgres`  
    `Password: postgres`  

9. In this newly created server, create a new database. Name it `codeassist`. This is important for `init_db.py`

10. Now in your `flask` container console, run `python3 init_db.py`. This should generate your tables in the codeassist database. You can check that it is populated in the pgadmin website. (under codeassist/Schemas/public/Tables)

11. Start the frontend service -- will automatically open the webpage
    In a NEW terminal  
    cd into the frontend folder and run:
    ```bash
    cd frontend
    ```

    ```bash
    npm start 
    ```

12. If you can access the website and can create a user, you can now begin development :bowtie:


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


