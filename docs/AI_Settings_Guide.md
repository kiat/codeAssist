# AI Settings Guide

## Purpose

AI Settings lets instructors configure AI feedback for programming assignments.

Supported providers:

* OpenAI / ChatGPT
* Google Gemini
* Anthropic Claude

AI feedback should focus on **correctness and debugging**, not style, formatting, readability, or refactoring.

---

## Key Files

### Frontend

```text
frontend/src/pages/instructor/aiSettings/index.js
frontend/src/pages/instructor/assignments/CreateAssignment.js
frontend/src/pages/assignmentSettings/index.js
frontend/src/services/course.js
```

### Backend

```text
backend/routes/course.py
backend/ai_feedback/integration.py
backend/api/models.py
backend/test/unit/test_course.py
```

---

## Course-Level AI Settings

Course-level settings are the default AI settings for a course.

Instructors can configure:

* Provider
* API key
* Default model
* Feedback style
* Temperature

Saved course fields:

```python
default_ai_provider
default_ai_model
openai_api_key
gemini_api_key
claude_api_key
default_feedback_style
default_ai_temperature
```

---

## Assignment-Level AI Settings

Each assignment can either:

1. Use course default AI settings.
2. Customize provider/model for that assignment only.

Assignment fields:

```python
ai_feedback_enabled
use_course_ai_default
ai_feedback_provider
ai_feedback_model
ai_feedback_prompt
ai_feedback_temperature
ai_feedback_style
ai_feedback_max_requests
ai_feedback_wait_seconds
```

Recommended default:

```text
Use course default
```

## AI Feedback Usage Limits

Instructors can configure how often students may request AI feedback for an assignment.

### Maximum Feedback Requests

`ai_feedback_max_requests` controls how many times each student can ask for AI feedback on an assignment.

* Empty/null: unlimited requests
* 0: AI feedback requests disabled
* Positive number: maximum requests per student

### Thinking Time Between Requests

`ai_feedback_wait_seconds` controls how many seconds students must wait before requesting AI feedback again.

* 0: no wait time
* Positive number: required wait time in seconds

These settings are stored at the assignment level. Student-facing enforcement, countdown display, and remaining request count will be handled in a follow-up student-side workflow.

---

## API Key Test vs Model Test

There are two separate tests because a valid API key does not guarantee the selected model works.

### Test API Key

Endpoint:

```text
POST /test_ai_api_key
```

Checks whether the provider API key is valid.

### Test Selected Model

Endpoint:

```text
POST /test_ai_model
```

Checks whether the selected provider/model can generate a response.

### Result Meaning

```text
API Key failed:
  Provider/key problem.

API Key passed, Model failed:
  Key is valid, but selected model is unavailable or unsupported.

Both passed:
  Provider/model is ready to use.
```

---

## Fetch Models

Endpoint:

```text
POST /fetch_ai_models
```

Use this before selecting a model.

Frontend note:

```text
Click Fetch Models first to load all available models.
Before fetching, the dropdown may only show the saved/default model.
```

Both pages use this backend route:

```text
Course AI Settings model dropdown
Create Assignment custom model dropdown
```

So model filtering should happen in the backend.

---

## Model Filtering Rules

Some provider APIs return models that appear available but cannot be used for this feedback workflow.

Filtering should be handled in:

```text
backend/routes/course.py
```

### OpenAI

Recommended:

```text
gpt-4o-mini
gpt-4o
gpt-4.1-mini
gpt-4.1
```

Avoid for now:

```text
o3-mini
o4-mini
```

Reason:

```text
They may reject max_tokens and require max_completion_tokens.
```

### Gemini

Recommended:

```text
gemini-1.5-flash
gemini-1.5-pro
gemini-2.5-flash
gemini-2.5-pro
```

Avoid:

```text
gemini-2.0-flash
deep-research models
antigravity models
embedding models
audio/image/video models
```

Reason:

```text
They may not support the standard generateContent feedback request.
```

### Claude

Recommended:

```text
claude-3-5-sonnet-20241022
claude-3-5-haiku-20241022
claude-3-opus-20240229
```

Avoid:

```text
claude-fable
claude-mythos
```

Also note:

```text
Some Claude models reject temperature in the request body.
Remove temperature from the Claude model test request.
```

---

## Prompt Behavior

If the assignment prompt is blank:

```text
Backend uses the built-in default prompt.
```

If the assignment prompt has text:

```text
Custom prompt replaces the default prompt.
```

It does **not** append to the default prompt.

The prompt should focus on:

* Incorrect logic
* Missing required behavior
* Failed tests
* Edge cases
* Runtime errors
* Incorrect input/output
* Incorrect return values
* Algorithm mistakes

The prompt should avoid:

* Style
* Formatting
* Naming
* Indentation
* Readability
* Refactoring

---

## Basic Testing

### Backend

From `backend`:

```bash
PYTHONPATH=. python -m pytest
```

### Frontend

From `frontend`:

```bash
npm test -- --watchAll=false
```

### Manual Check

Confirm:

```text
[ ] API key test works.
[ ] Selected model test works.
[ ] Fetch Models removes bad models.
[ ] Course default settings save and reload.
[ ] Assignment can use course default AI settings.
[ ] Assignment can use custom AI settings.
[ ] AI feedback appears or shows a clear error.
```

---

## Database Cleanup for Old Bad Models

Old saved models may still appear even after backend filtering.

Enter Postgres:

```bash
docker exec -it postgres_container psql -U postgres -d codeassist
```

Clean course defaults:

```sql
UPDATE courses
SET default_ai_model = 'gpt-4o-mini'
WHERE default_ai_provider = 'openai'
  AND default_ai_model IN ('o3-mini', 'o4-mini');

UPDATE courses
SET default_ai_model = 'gemini-1.5-flash'
WHERE default_ai_provider = 'gemini'
  AND (
    default_ai_model = 'gemini-2.0-flash'
    OR default_ai_model ILIKE '%deep-research%'
    OR default_ai_model ILIKE '%antigravity%'
  );
```

Clean assignment custom models:

```sql
UPDATE assignments
SET ai_feedback_model = NULL
WHERE ai_feedback_provider = 'openai'
  AND ai_feedback_model IN ('o3-mini', 'o4-mini');

UPDATE assignments
SET ai_feedback_model = NULL
WHERE ai_feedback_provider = 'gemini'
  AND (
    ai_feedback_model = 'gemini-2.0-flash'
    OR ai_feedback_model ILIKE '%deep-research%'
    OR ai_feedback_model ILIKE '%antigravity%'
  );
```

Exit:

```sql
\q
```

---

## Common Issues

### API key works, model fails

Meaning:

```text
The key is valid, but the selected model is unsupported or unavailable.
```

Fix:

```text
Fetch models again and choose another model.
```

### Bad model still appears

Meaning:

```text
The bad model is already saved in the database.
```

Fix:

```text
Clean courses or assignments table.
```

### OpenAI max_tokens error

Fix:

```text
Filter out o3-mini and o4-mini, or update backend to use max_completion_tokens.
```

### Gemini generateContent or JSON error

Fix:

```text
Filter out special models like deep-research, antigravity, embedding, audio, image, and video models.
```

### Claude temperature error

Fix:

```text
Remove temperature from Claude test request body.
```
