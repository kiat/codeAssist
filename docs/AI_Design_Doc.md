# CodeAssist AI Feature Design Doc

## Introduction
The **AI Feedback API** extends the existing CodeAssist system to provide LLM-powered, rubric-aligned feedback on students' programming submissions. It integrates with the existing CodeAssist pipeline to:
1. Run secure autograder tests in Docker containers.
2. Perform static checks for style and complexity using linters.
3. Invoke Large-Language Models (LLMs) to evaluate submissions against instructors' rubrics and for accuracy, and provide personalized feedback.


## Frontend
###  Menu design change (NEED TO BE DONE, refer ChatALL)

## AI Settings (Instructor View)

* API key input fields (OpenAI, Gemini, Claude, Local LLM).
* Save settings to backend.
* Option to toggle **“Enable AI Feedback”** on assignments.
* Dropdown to select **1 model (model_id)** for the assignment.
  * Example: Instructor sets `GPT-4o-mini` as default for Assignment 1.

**Backend Alignment**:
* `POST /assignments` includes `model_id`.

---

## AI Feedback Panel (Student View)

Since the model is already chosen by the instructor, **students don’t pick multiple models**.

### Students see:

* **Summary card** with general feedback (from `general_feedback`).
* **Inline code viewer** with line-level highlights (from `line_comments`).(Use a code editor component in frontend)
* **Rubric breakdown** (table or progress bars) from `rubric_breakdown`. (e.g., table: Correctness, Style, Efficiency).--> store it as JSON in backend → render it as table in frontend.

**Backend Alignment**:
* `GET /results/{result_id}` returns structured JSON for **one model’s output**.

#### Example rubric breakdown table: 

| Line | Rubric Item   | Score | Feedback                                   |  
|------|---------------|-------|--------------------------------------------|  
| 12   | Correctness   | -1    | Missing return value                       |  
| 12   | Efficiency    | -2    | Suggest using list comprehension           |  
| 20   | Style         | -0.5  | Variable naming not following convention   |  

#### Example JSON Response (Backend → Frontend): 

{
  "general_feedback": "Your solution works but can be optimized.",
  "rubric_breakdown": {
    "Correctness": 7,
    "Style": 8,
    "Efficiency": 6
  },
  "line_comments": [
    {"line": 12, "comment": "Consider using a loop instead of repeating code."},
    {"line": 20, "comment": "Variable name 'x' should be more descriptive."}
  ]
}


## Backend

Aligning with the existing system, our Python/Flask backend provides a suite of REST API endpoints to the frontend, and is connected to our PostgreSQL database. 

When a student submits code for their assignment, we save the file to the database, copy the file and the assignment autograder into a new docker image, execute the docker image in a container, and finally, store the result in our database and return it to the frontend.

### 1. Instructor defines assignment and rubric ###
**POST** `/assignments`
**POST** `/rubrics`
Assignments include configuration for sandbox execution. The Rubric will define weighted criteria and be used in the process of generating feedback.

### 2. Student submits their solution ###
**POST** `/submissions`

### 3. CodeAssist runs grading pipeline ###
Once CodeAssist runs the grading pipeline,
- sandbox executes autograder tests
- static analysis runs
- AI evaluates rubric criteria as well as code optimacy

### Results are retrieved as ###
**GET** `/results/{result_id}`
Final score, per-criterion feedback, and inline comments will be offered.

## Endpoints
### Make submissions (Preexisting)
**POST** `/submissions`
This still creates an asynchronous grading job that runs the sandbox autograder, static checks, and now the selected LLM. 

### Get submission status (Preexisting, but extended)
**GET** `/submissions/{submission_id}`
Similarly, this is an existing endpoint already built in CodeAssist to check the status of student submissions. When combined with AI grading, this endpoint also obtains the `result_id` once available.

### Get results
**GET** `/results/{result_id}`
Retrieves the full grading output, including unit tests, rubric scoring, and algorithmic feedback.

### List supported models
**GET** `/models`
Returns available `model_id` values and guidance so instructors can choose for each of their assignments.

### Create assignment (Preexisting, but extended)
**POST** `/assignments`
While already preexisting, an assignment description text will be requested additionally. When an AI grading job runs, the backend fetches this description from the database and passes it into the LLM prompt so that rubric evaluation and algorithm feedback are grounded in the instructor's assignment wordings. In addition, this endpoint also establishes assignment-level defaults used for AI feedback:
- `model_id`: chosen LLM (default will be set to gpt-4o-mini)
- `rubric_id`: the rubric scheme linked to the assignment 


### Create rubric
**POST** `/rubrics`
Attaches a rubric scheme to an assignment.


## LLMs
With the rapid development of varying LLMs, different models excel at different programming languages and rubric styles. To give instructors and students more flexibility, CodeAssist offers a list of supported LLMs that users can choose from. The model selected by instructor while creating the assignment processes the structured grading tasks and produces rubric‑aligned, verifiable feedback. The selection of an LLM is implemented as a checkbox, with one selected only for each assignment. 

- Currently, models supported are:
  - openai:
  - gemini:

- All LLMs must return structured JSON, parsed and validated by the backend.
- Feedback prompts include assignment description, rubric criteria, test results, and static check summaries. The feedback also asks LLMs to provide feedback on code quality so that students learn how to make their code more optimal.
