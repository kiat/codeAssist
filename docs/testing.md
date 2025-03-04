# CodeAssist Testing
Testing suite is currently configured to run in root directory with:
```
make test
```

### Backend testing
The current package being used is `pytest`, as well as `pytest-mock` for mocking and `pytest-cov` for coverage.
- Unit tests can be found in `/backend/test/unit`
    - Unit tests verify the logical flow of endpoints using mocked dependencies (i.e. the correct methods are being called the correct number of times).
    - This is especially important to make sure new changes don't inadvertently alter old logic.
    - In practice, all possible cases should be tested, which is necessary for high coverage anyways.
- Integration tests can be found in `/backend/test/it`
    - Integration tests ensure proper interaction between different services. 
    - Dependencies are no longer mocked, and endpoints interact directly with an in-memory SQLite database configured by `/backend/config.py`.

Run configurations can be found in `/backend/pytest.ini`.


### Frontend testing
TODO

### End-to-End testing
TODO