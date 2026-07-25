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

### Testing Structure
- Using Pytest Mocker: 
- EX: # backend/services/email_sender.py
      def send_email(to: str, msg: str) -> bool:
        return external_email_lib.send(to, msg)

You don’t want to really send an email, so you mock it:

- EX: from backend.services.email_sender import send_email

      def test_send_email_success(mocker):
          mock_send = mocker.patch("external_email_lib.send", return_value=True)
          
          result = send_email("test@example.com", "Hello!")

          assert result is True
          mock_send.assert_called_once_with("test@example.com", "Hello!")

- Using Pytest:
- EX: # frontend/utils.py

      def capitalize_name(name: str) -> str:
          if not name:
              return ""
          return name[0].upper() + name[1:].lower()

You just want to assert the input of the function you want to test with the expected output:

- EX: from frontend.utils import capitalize_name

      def test_capitalize_name_basic():
          assert capitalize_name("john") == "John"
          assert capitalize_name("DOE") == "Doe"
          assert capitalize_name("aLiCe") == "Alice"

      def test_capitalize_name_empty():
          assert capitalize_name("") == ""

- Useful Tips:
  - Organize the files so that testing integrity is maintained.
  - Use LLMs to rewrite repetitive tasks, they usually fail first time so you need to go through to debug. 

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
The current package being used is `pytest`, as well as `pytest-mock` for mocking and `pytest-cov` for coverage.
- Unit tests can be found in `/frontend/test/..`
    - Unit tests verify the logical flow and behavior of frontend components and utility functions using mocked dependencies.
  - This ensures that components render correctly and logic executes as expected, even when isolated from external APIs or services.
  - All possible edge and normal cases should be tested to maintain high reliability and coverage.
- Integration tests may include tests for component interactions or API integrations using tools like pytest-playwright or mocking fetch/XHR calls, but are not currently emphasized.
    - Integration tests ensure proper interaction between different services. 
    - Run configurations are defined in the Makefile and managed via pytest.ini in the frontend directory (if present).
- Run configurations can be found in `/frontend/pytest.ini`.
- Current testing results (7/24 meeting):
-------------------------------------|---------|----------|---------|---------|-------------------------------------------------------------------------------
File                                 | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s                                                             
-------------------------------------|---------|----------|---------|---------|-------------------------------------------------------------------------------
All files                            |    19.7 |     9.63 |   17.07 |   20.08 |                                                                               
 src                                 |   17.24 |        0 |       0 |   19.23 |                                                                               
  App.js                             |   17.24 |        0 |       0 |   19.23 | 43-179                                                                        
 src/common                          |     100 |      100 |     100 |     100 |                                                                               
  format.js                          |     100 |      100 |     100 |     100 |                                                                               
 src/components                      |   47.69 |    46.66 |   51.72 |   48.06 |                                                                               
  FileUpload.js                      |     100 |      100 |     100 |     100 |                                                                               
  LoadingOverlay.js                  |     100 |      100 |     100 |     100 |                                                                               
  RegradeRequests.js                 |       0 |        0 |       0 |       0 | 8-80                                                                          
  TestResult.js                      |     100 |      100 |     100 |     100 |                                                                               
  TestResults.js                     |     100 |      100 |     100 |     100 |                                                                               
  UploadModal.js                     |   33.82 |    16.66 |   36.36 |   33.82 | 43-61,69-73,84-91,96-99,103-125,129-147,164-185                               
 src/components/download             |       0 |      100 |       0 |       0 |                                                                               
  PopoverDownload.js                 |       0 |      100 |       0 |       0 | 5                                                                             
 src/components/layout               |    4.65 |        0 |      10 |    4.76 |                                                                               
  CollapsedSidebar.js                |       0 |        0 |       0 |       0 | 6                                                                             
  ExpandedSidebar.js                 |       0 |        0 |       0 |       0 | 10-14                                                                         
  GradeSider.js                      |       0 |        0 |       0 |       0 | 14-53                                                                         
  accountPopoverContent.js           |       0 |      100 |       0 |       0 | 11-40                                                                         
  pageBottom.js                      |     100 |      100 |     100 |     100 |                                                                               
  pageContent.js                     |     100 |      100 |     100 |     100 |                                                                               
  sider.js                           |       0 |        0 |       0 |       0 | 8-35                                                                          
 src/config                          |     100 |      100 |     100 |     100 |                                                                               
  url.js                             |     100 |      100 |     100 |     100 |                                                                               
 src/mock                            |   55.17 |        0 |    12.5 |   55.17 |                                                                               
  assignment.js                      |   66.66 |      100 |       0 |   66.66 | 9                                                                             
  assignmentResult.js                |      50 |      100 |       0 |      50 | 7,15,26                                                                       
  common.js                          |   28.57 |        0 |      50 |   28.57 | 9-14                                                                          
  constant.js                        |     100 |      100 |     100 |     100 |                                                                               
  course.js                          |   42.85 |        0 |       0 |   42.85 | 9,20-27                                                                       
  index.js                           |       0 |        0 |       0 |       0 |                                                                               
 src/pages/assignmentSettings        |       0 |        0 |       0 |       0 |                                                                               
  index.js                           |       0 |        0 |       0 |       0 | 23-367                                                                        
 src/pages/assignments               |   71.42 |    45.23 |   70.96 |   71.17 |                                                                               
  assignment_modal.js                |   66.66 |    16.66 |   66.66 |   66.66 | 13-17,23-24,46-47,71                                                          
  constant.js                        |     100 |      100 |     100 |     100 |                                                                               
  index.js                           |   71.05 |    43.75 |      65 |   70.66 | 22,34,41,48,55,62,79-80,85-86,113,116,119-120,130-131,145-146,173,178-179,184 
 src/pages/configureAutograder       |       0 |        0 |       0 |       0 |                                                                               
  TestAutograder.js                  |       0 |        0 |       0 |       0 | 4-53                                                                          
  index.js                           |       0 |        0 |       0 |       0 | 26-108                                                                        
 src/pages/createRubric              |       4 |        0 |       0 |    4.25 |                                                                               
  FormattingCard.js                  |       0 |        0 |       0 |       0 | 14-76                                                                         
  ImportRubric.jsModal.js            |       0 |        0 |       0 |       0 | 6-97                                                                          
  RubricOptions.js                   |       0 |      100 |       0 |       0 | 4                                                                             
  index.js                           |    4.16 |      100 |       0 |    4.54 | 44-132                                                                        
  mock.js                            |     100 |      100 |     100 |     100 |                                                                               
 src/pages/dashboard                 |   86.79 |    58.33 |   84.21 |   86.53 |                                                                               
  addCourseModal.js                  |     100 |      100 |     100 |     100 |                                                                               
  addForm.js                         |     100 |      100 |     100 |     100 |                                                                               
  constant.js                        |     100 |      100 |     100 |     100 |                                                                               
  courseModal.js                     |       0 |      100 |       0 |       0 | 4                                                                             
  index.js                           |   86.95 |    58.33 |   84.61 |   86.66 | 44-45,81-86,123                                                               
  relationForm.js                    |     100 |      100 |     100 |     100 |                                                                               
  relationModal.js                   |     100 |      100 |     100 |     100 |                                                                               
 src/pages/dashboard/semesterCourses |   14.28 |        0 |       0 |    14.7 |                                                                               
  course.js                          |   41.66 |        0 |       0 |   41.66 | 49-65                                                                         
  index.js                           |       0 |        0 |       0 |       0 | 4-73                                                                          
 src/pages/editAccount               |       0 |        0 |       0 |       0 |                                                                               
  index.js                           |       0 |        0 |       0 |       0 | 24-126                                                                        
 src/pages/editOutline               |       0 |        0 |       0 |       0 |                                                                               
  index.js                           |       0 |        0 |       0 |       0 | 18-83                                                                         
 src/pages/extensions                |       0 |        0 |       0 |       0 |                                                                               
  ExtensionModal.js                  |       0 |        0 |       0 |       0 | 24-132                                                                        
  index.js                           |       0 |        0 |       0 |       0 | 25-241                                                                        
 src/pages/gradeSubmissions          |      75 |       75 |   61.11 |   76.92 |                                                                               
  GradingDashboard.js                |     100 |      100 |     100 |     100 |                                                                               
  Question.js                        |   70.58 |      100 |   58.33 |   68.75 | 27,37,43-49                                                                   
  index.js                           |      60 |       50 |   33.33 |      75 | 10                                                                            
  mock.js                            |     100 |      100 |     100 |     100 |                                                                               
 src/pages/home                      |    92.1 |    66.66 |      90 |   91.89 |                                                                               
  index.js                           |   93.75 |      100 |   83.33 |   93.33 | 30                                                                            
  logInModal.js                      |    90.9 |       50 |     100 |    90.9 | 33                                                                            
  signUpModal.js                     |    90.9 |       50 |     100 |    90.9 | 32                                                                            
 src/pages/instructor/assignments    |       2 |        0 |       0 |    2.12 |                                                                               
  Assignments.js                     |    4.54 |        0 |       0 |    4.54 | 14-79                                                                         
  CreateAssignment.js                |    7.69 |        0 |       0 |    7.69 | 40-230                                                                        
  DuplicateAssignmentModal.js        |       0 |        0 |       0 |       0 | 8-94                                                                          
  index.js                           |       0 |        0 |       0 |       0 | 11-67                                                                         
 src/pages/instructor/courseSettings |       0 |        0 |       0 |       0 |                                                                               
  index.js                           |       0 |        0 |       0 |       0 | 29-290                                                                        
 src/pages/instructor/dashboard      |    7.69 |        0 |       0 |     8.1 |                                                                               
  TextItem.js                        |       0 |      100 |       0 |       0 | 5                                                                             
  constant.js                        |     100 |      100 |     100 |     100 |                                                                               
  index.js                           |    2.77 |        0 |       0 |    2.94 | 24-102                                                                        
 src/pages/instructor/enrollment     |    1.81 |        0 |       0 |    1.86 |                                                                               
  AddCSVModal.js                     |    2.22 |        0 |       0 |    2.22 | 7-92                                                                          
  AddMoreUsersModal.js               |       0 |        0 |       0 |       0 | 9-55                                                                          
  AddUserModal.js                    |       0 |      100 |       0 |       0 | 12                                                                            
  index.js                           |    1.78 |        0 |       0 |    1.88 | 36-190                                                                        
 src/pages/manageSubmissions         |    1.75 |        0 |       0 |    1.88 |                                                                               
  RerunAutograderModal.js            |       0 |      100 |       0 |       0 | 5                                                                             
  index.js                           |    1.78 |        0 |       0 |    1.92 | 25-168                                                                        
 src/pages/result                    |    0.73 |        0 |       0 |    0.76 |                                                                               
  ActionButtons.js                   |       0 |        0 |       0 |       0 | 5                                                                             
  FormattingModal.js                 |      50 |      100 |       0 |      50 | 24                                                                            
  StudentInfoPanel.js                |       0 |        0 |       0 |       0 | 16-254                                                                        
  TestResultsDisplay.js              |    1.57 |        0 |       0 |     1.6 | 15-309                                                                        
  index.js                           |       0 |        0 |       0 |       0 | 19-287                                                                        
  submissionHistoryModal.js          |       0 |        0 |       0 |       0 | 7-188                                                                         
 src/pages/reviewGrades              |      66 |    61.11 |   54.16 |   68.75 |                                                                               
  DownloadSubmissions.js             |     100 |      100 |     100 |     100 |                                                                               
  index.js                           |   64.58 |    61.11 |   52.17 |   67.39 | 31,39,45-49,62,68,78,84,94,102,109,121-122,131,139                            
  mock.js                            |     100 |      100 |     100 |     100 |                                                                               
 src/services                        |    7.89 |        0 |       0 |    7.89 |                                                                               
  assignment.js                      |       0 |      100 |       0 |       0 | 4-20                                                                          
  course.js                          |       0 |      100 |       0 |       0 | 4-48                                                                          
  index.js                           |      20 |        0 |       0 |      20 | 11-31,44                                                                      
  submission.js                      |       0 |      100 |       0 |       0 | 4-8                                                                           
  user.js                            |       0 |      100 |       0 |       0 | 4-16                                                                          
-------------------------------------|---------|----------|---------|---------|-------------------------------------------------------------------------------

Test Suites: 21 passed, 21 total
Tests:       49 passed, 49 total
Snapshots:   0 total
Time:        6.125 s

### End-to-End testing
TODO
