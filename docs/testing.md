# CodeAssist Testing
Testing suite is currently configured to run after all initial setup has been completed in root directory with:
```
make test
```
Prerequisites:
- docker must be set up and running
    - docker can be run in the backend directory with:
    ```
    docker compose up
    ```


### Backend testing
The current package being used is `pytest`, as well as `pytest-mock` for mocking and `pytest-cov` for coverage.
- Unit tests can be found in `/backend/test/unit`
    - Unit tests verify the logical flow of endpoints using mocked dependencies (i.e. the correct methods are being called the correct number of times).
    - This is especially important to make sure new changes don't inadvertently alter old logic.
    - In practice, all possible cases should be tested, which is necessary for high coverage anyways.
    - Current unit tests are test_assignment.py, test_course.py, test_user.py, test_submission.py, test_regrade_request.py
        - backend/tests/unit/
          ├── test_assignment.py
          ├── test_course.py
          ├── test_user.py
          ├── test_submission.py
          └── test_regrade_request.py
- Integration tests can be found in `/backend/test/it`
    - Integration tests ensure proper interaction between different services. 
    - Dependencies are no longer mocked, and endpoints interact directly with an in-memory SQLite database configured by `/backend/config.py`.
- Run configurations can be found in `/backend/pytest.ini`.
- Current testing results (4/25 meeting):
    Name                        Stmts   Miss  Cover
    -----------------------------------------------
    routes/__init__.py             12      0   100%
    routes/assignment.py          163      4    98%
    routes/course.py              262     50    81%
    routes/regrade_request.py     104     12    88%
    routes/submission.py          277    150    46%
    routes/user.py                 85      9    89%
    -----------------------------------------------
    TOTAL                         903    225    75%
- Adding new tests
    - Create new python file in backend/tests/unit/test_<endpoint>.py.
    - Cover success path, validation errors, and edge cases.


### Frontend testing
TODO

### End-to-End testing
TODO