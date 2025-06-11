
# How to Use the Autograder

The autograder system is designed to handle the submission of student assignments and to evaluate them using Docker containers.

## Setup
1. **Python and Flask**: Ensure Python and Flask are installed on your system to handle HTTP requests.
2. **Docker**: Docker must be installed and running to handle the isolation and execution of the grading scripts.

## API Endpoints

### Upload a Submission
The `/upload_submission` endpoint allows students to submit their assignments. The server receives files and student metadata, and then proceeds to process and evaluate the submission inside a Docker container.

#### Steps:
1. **File Upload**: A POST request is made with a multipart file upload including the student's work.
2. **Directory Setup**: Directories for storing submissions and results are created based on the assignment ID and student ID.
3. **Dockerfile Writing and Image Building**: A Dockerfile is generated dynamically to set up the environment needed for running the student's code.
4. **Container Management**: A Docker container is run using the newly built image. The student's submission is executed inside this container.
5. **Result Handling**: Results of the grading process are saved back to the server, and a summary is provided to the student.

### Upload an Autograder
The `/upload_assignment_autograder` endpoint allows instructors to upload and update the autograder scripts and test cases packaged as a ZIP file.

#### Steps:
1. **File Validation and Upload**: Validate and store the uploaded ZIP file.
2. **Setup Execution Environment**: Extract the contents of the ZIP file and prepare the environment required for executing the autograder scripts.

## Error Handling
Both endpoints include error handling to manage scenarios like missing files, incomplete parameters, or failures during file processing and Docker operations.

## Security Notes
1. **Secure Filename**: Use `secure_filename` from Werkzeug to sanitize file names.
2. **Cross-Origin Resource Sharing (CORS)**: Managed by `cross_origin` to allow requests from different origins, useful in a development or educational setting.


### Conclusion
This autograder setup provides a robust and isolated environment for assignment evaluation, leveraging modern technologies like Docker for consistent and scalable performance.

## API Test Cases

The autograder system includes a set of API tests designed to validate the functionality of endpoints for uploading autograders and submissions. These tests ensure that the endpoints handle requests correctly and respond appropriately to various input scenarios.

### Overview of Tests
- **Test Setup**: Before the tests, an instructor, a student, and a course are created. Assignments `A1` and `A2` are then added to the course.

### Test Details

#### 1. Upload Autograder for Assignment A1
- **Purpose**: To test the uploading of an autograder ZIP file for assignment `A1`.
- **Method**: POST
- **Endpoint**: `/upload_assignment_autograder`
- **Data**: Assignment ID for `A1` and the ZIP file containing the autograder scripts.

#### 2. Upload Submission for Assignment A1
- **Purpose**: To test the submission upload functionality for a student's work on assignment `A1`.
- **Method**: POST
- **Endpoint**: `/upload_submission`
- **Data**: Assignment ID for `A1`, student ID, and the file containing the student's submission.

#### 3. Upload Autograder for Assignment A2
- **Purpose**: To test the uploading of an autograder ZIP file for assignment `A2`.
- **Method**: POST
- **Endpoint**: `/upload_assignment_autograder`
- **Data**: Assignment ID for `A2` and the ZIP file containing the autograder scripts.

#### 4. Upload Submission for Assignment A2
- **Purpose**: To test the submission upload functionality for a student's work on assignment `A2`.
- **Method**: POST
- **Endpoint**: `/upload_submission`
- **Data**: Assignment ID for `A2`, student ID, and the file containing the student's submission.

### Running the Tests
These tests can be executed using the Python testing `unittest`. Each test is designed to verify that the system correctly processes and responds to API requests, ensuring the reliability and efficiency of the autograder system.


## Alembic Migration Tool

Alembic is a lightweight database migration tool for use with the SQLAlchemy Database Toolkit for Python. It is designed to allow controlled upgrades and downgrades of database schemas through changes in Python code.

### Key Concepts
- **Migration Script**: A Python script that describes changes to the database. These scripts are used by Alembic to apply or revert a set of changes.
- **Migration Environment**: The environment configuration that Alembic uses to run migrations, which includes settings from an `.ini` configuration file.

### Configuration Steps
1. **Logging Setup**: Configures Python's logging to use the settings from the Alembic `.ini` file.
2. **Database URL**: Ensures that the database URL is specified as an environment variable (`DATABASE_URL`). This URL is crucial for Alembic to connect to the database.
3. **Metadata Object**: Alembic needs a metadata object from your SQLAlchemy models to perform automatic migrations.

### Running Migrations
Alembic can execute migrations in two modes:
- **Offline Mode**: Run migrations without connecting to a database. This is useful for generating SQL scripts that can be executed manually.
- **Online Mode**: Connect to a database and apply migrations directly.

#### Example Usage
To run migrations online, ensure that the `DATABASE_URL` environment variable is set and use the following command:
```bash
alembic upgrade head
```

### Integration with Flask
For Flask applications, Alembic can be integrated to handle database migrations seamlessly alongside the application's development and deployment phases.

