# Student History and AI Memory Future Work

## Goal

Student history and AI memory would let CodeAssist include relevant past learning context when generating AI feedback. This is future work. The current PR should continue to focus on configurable prompts and instructor-controlled context inputs, not production memory retrieval.

This design covers the shape of a later feature without adding LangChain, embeddings, vector search, student-facing memory UI, or automatic long-term memory.

## Feature Summary

Future AI feedback could optionally use historical context for the current student, course, and assignment. Useful context may include:

- previous submissions
- previous AI feedback
- previous AI conversations
- repeated mistakes
- assignment history
- course history

Example future prompt context:

```text
This is student John Doe, ID xxx.
Here is the current assignment.
Here is the current submission.
Here are the student's previous submissions.
Here are repeated mistakes from previous feedback.
Here is relevant assignment and course history.
```

The AI should use this context only when it directly improves feedback. It should not dump the student's history into the response or mention private details unnecessarily.

## Why This Is Useful

Student history can make feedback more personalized and consistent:

- If a student repeatedly struggles with recursion, feedback can acknowledge that pattern and focus on base cases or recursive structure.
- If a student often misses edge cases, feedback can remind them to test boundary conditions.
- If a student improved from earlier submissions, feedback can acknowledge progress.
- If similar advice was already given before, feedback can avoid repeating the exact same generic message.

The goal is better teaching support, not surveillance or broad profiling. Historical context should be compact, relevant, and scoped to the learning task.

## Why This Is Future Work

This feature is larger than configurable prompts and context controls because it requires:

- database design for storing feedback and conversation history
- privacy rules and permission checks
- instructor controls for enabling or disabling history use
- memory retrieval logic scoped to the current student and course
- summarization for long histories
- safeguards against leaking student data
- prompt-size management
- retention and deletion rules
- auditability for what history was included

The current PR should not implement production memory retrieval. It should keep the existing AI feedback flow unchanged.

## Backend Design Proposal

The future backend can expose a service contract like this:

```python
class StudentHistoryService:
    def get_student_history_context(
        self,
        student_id: str,
        course_id: str,
        assignment_id: str,
        limit: int = 5,
    ) -> dict:
        """
        Return relevant historical context for one student in one course.
        This future-work interface must not expose data from other students.
        """
```

The safe default structure should be:

```python
{
    "previous_submissions": [],
    "previous_feedback": [],
    "previous_conversations": [],
    "repeated_mistakes": [],
    "course_history_summary": "",
    "assignment_history_summary": "",
}
```

The placeholder implementation in `backend/ai_feedback/student_history.py` intentionally returns this empty structure. It does not query production data and is not wired into existing AI feedback generation.

The same module also includes pure helper functions for future integration:

- `normalize_student_history_context(...)` filters context to approved keys, applies safe defaults, and copies list values.
- `render_student_history_context(...)` formats non-empty history sections for prompt construction and returns a safe empty message when no history is available.
- `build_student_history_retrieval_documents(...)` creates provider-neutral document dictionaries with `page_content` and scoped metadata. A future LangChain integration could convert these dictionaries into LangChain `Document` objects without changing the storage contract.

The helper layer is intentionally defensive:

- history lists are capped by a bounded `limit`
- item dictionaries are filtered through per-section allowlists
- raw code, private chat transcripts, names, emails, and other sensitive keys are not copied into prompt context
- long text values are truncated before rendering
- retrieval document metadata always includes `student_id`, `course_id`, `assignment_id`, `history_key`, and `memory_scope`

Future production retrieval should:

- require `student_id`, `course_id`, and `assignment_id` scope
- check that student-history memory is enabled for the assignment or course
- check the authenticated user's permissions
- query only approved tables and columns
- summarize long history before prompt construction
- return compact structured context instead of raw unbounded records

## Privacy and Permission Rules

Student history memory should follow these rules:

- The AI should only receive history for the current authenticated student.
- Memory retrieval must be scoped by `student_id`, `course_id`, and `assignment_id`.
- Student history should only be used when the instructor enables it.
- The system should clearly define what history is included.
- The system should avoid sending unnecessary personal data to AI providers.
- Instructors may view course-level trends, but one student's private AI conversations must never be exposed to another student.
- Long-term memory needs retention and deletion rules.
- Logs should avoid storing sensitive prompt content unless necessary.
- Debug logs should not print raw student history or private conversations.
- Any future exports should distinguish aggregate trends from individual student records.

## Prompt Context Design

A future prompt could be assembled from separate, instructor-approved sections:

```text
System prompt:
You are an AI teaching assistant for a programming course.

Assignment context:
{assignment_description}
{rubric}
{starter_code}

Current submission:
{student_code}

Student history context:
{previous_submission_summary}
{previous_feedback_summary}
{repeated_mistakes}

Instruction:
Give feedback on the current submission. Use student history only when it is directly relevant. Do not mention private data unnecessarily.
```

Prompt construction should preserve the existing context-control model. Student history should be a separate opt-in input, not an implicit addition to every feedback request.

Important behavior:

- Use history to improve feedback, not to summarize a student's record.
- Prefer summaries and tags over raw conversation transcripts.
- Include only the minimum relevant history needed for the current request.
- Avoid adding history when it would not change the feedback.
- Keep provider prompts within size limits.

## Repeated Mistake Detection

Future repeated-mistake tracking could identify patterns such as:

- missing edge cases
- incorrect recursion base case
- poor variable naming when it affects readability or correctness
- inefficient algorithm
- syntax errors
- misunderstanding assignment requirements
- weak test coverage
- repeated style issues

Detection options:

1. Simple rule-based detection from previous feedback tags.
2. AI-generated summary after each feedback session.
3. Database fields storing mistake categories.
4. Later retrieval or LangChain memory over stored summaries.

Recommended first version:

Store structured feedback tags when AI feedback is generated.

```json
{
  "mistake_tags": ["edge_cases", "recursion", "time_complexity"],
  "summary": "Student often handles the main case correctly but misses boundary cases."
}
```

These tags are easier to filter, permission-check, summarize, and test than unstructured long-term memory.

## Database Design Proposal

Exact schema should be adjusted to the existing CodeAssist models and migrations. A possible future design:

### `ai_feedback_history`

Stores previous feedback results.

Possible fields:

- `id`
- `student_id`
- `course_id`
- `assignment_id`
- `submission_id`
- `feedback_text`
- `rubric_breakdown`
- `mistake_tags`
- `created_at`

### `ai_conversation_history`

Stores AI chat interactions when chat memory is enabled.

Possible fields:

- `id`
- `student_id`
- `course_id`
- `assignment_id`
- `message_role`
- `message_content`
- `created_at`

### `student_learning_summary`

Stores compressed memory summaries for each student and course.

Possible fields:

- `id`
- `student_id`
- `course_id`
- `summary_text`
- `repeated_mistakes`
- `strengths`
- `last_updated_at`

These tables should be added only after privacy behavior, instructor controls, and retention rules are finalized.

## LangChain Future Layer

LangChain should be treated as a future orchestration layer, not the foundation of the current PR. The current PR should focus on prompt configuration and context controls. Once student history storage and privacy rules are clearly designed, LangChain could be added later to retrieve relevant context, summarize prior feedback, and manage multi-step AI workflows.

Possible future LangChain use cases:

- retrieve the most relevant past submissions
- summarize previous AI feedback
- call tools such as an autograder, rubric checker, and code analyzer
- manage multi-step feedback generation
- apply memory only when instructor settings allow it

The current placeholder code does not import LangChain. It only provides a future-compatible document shape:

```python
{
    "page_content": "Repeated mistakes:\n- ...",
    "metadata": {
        "source": "student_history.repeated_mistakes",
        "student_id": "student-1",
        "course_id": "course-1",
        "assignment_id": "assignment-1",
        "history_key": "repeated_mistakes",
        "memory_scope": "student_course_assignment",
    },
}
```

LangChain should not bypass CodeAssist's database scoping, permission checks, retention rules, or instructor controls.

## Testing Plan

Any future service should have unit tests that do not call external AI APIs.

Current placeholder tests cover:

- default student history context returns a safe empty structure
- missing student or course scope returns the safe empty structure
- context structure includes expected keys
- returned lists are fresh per call
- unknown and sensitive item fields are filtered out
- history list rendering respects bounded limits
- long text values are truncated
- future retrieval documents include scoped metadata and require student/course/assignment scope

Future production tests should also cover:

- no data is returned across student boundaries
- no data is returned across course boundaries
- disabled history settings prevent retrieval
- prompt construction includes history only when enabled
- long histories are summarized or limited
- existing AI feedback behavior remains unchanged when memory is disabled

## Acceptance Criteria

This future-work foundation is complete when:

- clear documentation exists for student history and AI memory
- previous submissions, feedback, conversations, repeated mistakes, assignment history, and course history are described
- privacy and permission requirements are documented
- the documentation explains why this is future work
- LangChain is clearly marked as optional future work
- any placeholder service returns safe empty context by default
- existing configurable prompt and context-control behavior is unchanged
