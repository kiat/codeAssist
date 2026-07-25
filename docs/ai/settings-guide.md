# AI Settings Guide (Instructor Side)

> Moved from `docs/AI_Settings_Guide.md`. This is part 1 of the AI feature — see `README.md` in this folder for the full picture: instructors set API keys and pick prompts/models here (part 1); students then see feedback via file upload or the code editor (part 2, see `code-editor-feedback.md` and `architecture.md`).

## Purpose

AI Settings lets instructors configure AI feedback for programming assignments.

Supported providers:

* OpenAI / ChatGPT
* Google Gemini
* Anthropic Claude
* Ollama (self-hosted/local models)

AI feedback should focus on **correctness and debugging**, not style, formatting, readability, or refactoring.

---

## Key Files

### Frontend

```text
frontend/src/pages/instructor/aiSettings/index.js
frontend/src/pages/instructor/assignments/CreateAssignment.js
frontend/src/pages/assignmentSettings/index.js
frontend/src/components/AIFeedbackSettingsSection.js
frontend/src/constants/aiFeedbackSettings.js
frontend/src/services/course.js
```

### Backend

```text
backend/routes/course.py
backend/routes/ai_feedback.py
backend/routes/assignment.py
backend/ai_feedback/settings.py
backend/ai_feedback/integration.py
backend/api/models.py
backend/test/unit/test_course.py
```

---

## Course-Level AI Settings

Course-level settings are the default AI settings for a course — this is where API keys live.

Instructors can configure:

* Provider
* API key (stored encrypted — see `docs/encryption.md`)
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
ollama_base_url
default_feedback_style
default_ai_temperature
```

---

## Assignment-Level AI Settings

Each assignment can either:

1. Use course default AI settings (`use_course_ai_default = True`, recommended default).
2. Customize provider/model/prompts/limits for that assignment only.

Assignment fields:

```python
ai_feedback_enabled
use_course_ai_default
ai_feedback_provider
ai_feedback_model
ai_feedback_prompt          # legacy single-prompt field, kept for backwards compatibility
ai_feedback_prompts         # current: list of {id, title, prompt, enabled}
ai_allowed_inputs           # {assignment_description, student_code, test_results, test_cases, student_output}
ai_feedback_temperature
ai_feedback_style
ai_feedback_max_requests
ai_feedback_wait_seconds
```

**Gap to know about:** there is currently no `description`/instructions field on `Assignment` at all (not `ai_feedback_prompt`, an actual assignment-text field). Prompts above are the AI's *instructions*; they are not the assignment's problem statement. See `README.md` gap #1 — right now the AI only ever sees the assignment's *name*, not real assignment text, unless that's fixed.

## AI Feedback Usage Limits

* `ai_feedback_max_requests` — empty/null = unlimited, `0` = disabled, positive up to 1000 = per-student cap.
* `ai_feedback_wait_seconds` — `0` = no wait, positive = required cooldown seconds between requests.

Enforced server-side; student-facing remaining-count and countdown UI live in `AIChatPanel.js`.

---

## API Key Test vs Model Test

Two separate tests because a valid API key does not guarantee the selected model works.

### Test API Key — `POST /test_ai_api_key`
Checks whether the provider API key is valid.

### Test Selected Model — `POST /test_ai_model`
Checks whether the selected provider/model can generate a response.

### Result Meaning

```text
API Key failed:            Provider/key problem.
API Key passed, Model failed:  Key valid, model unavailable/unsupported.
Both passed:                Provider/model ready to use.
```

---

## Fetch Models — `POST /fetch_ai_models`

Use before selecting a model. Before fetching, the dropdown may only show the saved/default model. Both the Course AI Settings model dropdown and the Create Assignment custom model dropdown call this same backend route, so model filtering happens centrally in `backend/routes/course.py`.

---

## Model Filtering Rules

Some provider APIs return models that appear available but can't actually be used for this feedback workflow.

### OpenAI
- Recommended: `gpt-4o-mini`, `gpt-4o`, `gpt-4.1-mini`, `gpt-4.1`
- Avoid: `o3-mini`, `o4-mini` (may reject `max_tokens`, require `max_completion_tokens`)

### Gemini
- Recommended: `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.5-flash`, `gemini-2.5-pro`
- Avoid: `gemini-2.0-flash`, deep-research models, antigravity models, embedding/audio/image/video models (may not support standard `generateContent`)

### Claude
- Recommended: `claude-3-5-sonnet-20241022`, `claude-3-5-haiku-20241022`, `claude-3-opus-20240229`
- Avoid: `claude-fable`, `claude-mythos`
- Note: some Claude models reject `temperature` in the request body — it's intentionally omitted from Claude requests in `integration.py`.

---

## Prompt Behavior

If the assignment prompt is blank, the backend uses the built-in default prompt. If it has text, the custom prompt **replaces** (does not append to) the default.

Prompt should focus on: incorrect logic, missing required behavior, failed tests, edge cases, runtime errors, incorrect input/output, incorrect return values, algorithm mistakes.

Prompt should avoid: style, formatting, naming, indentation, readability, refactoring.

---

## Basic Testing

```bash
# Backend, from `backend`
PYTHONPATH=. python -m pytest

# Frontend, from `frontend`
npm test -- --watchAll=false
```

### Manual Check

- [ ] API key test works.
- [ ] Selected model test works.
- [ ] Fetch Models removes bad models.
- [ ] Course default settings save and reload.
- [ ] Assignment can use course default AI settings.
- [ ] Assignment can use custom AI settings.
- [ ] AI feedback appears or shows a clear error, via **both** file upload and code editor submission.

---

## Database Cleanup for Old Bad Models

If old saved models still appear after backend filtering was added:

```bash
docker exec -it postgres_container psql -U postgres -d codeassist
```

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

---

## Common Issues

**API key works, model fails** — key is valid, selected model is unsupported/unavailable. Fetch models again and choose another.

**Bad model still appears** — already saved in DB. Clean courses/assignments table (above).

**OpenAI max_tokens error** — filter out `o3-mini`/`o4-mini`, or update backend to use `max_completion_tokens`.

**Gemini generateContent or JSON error** — filter out deep-research/antigravity/embedding/audio/image/video models.

**Claude temperature error** — remove `temperature` from the Claude request body (already done in `integration.py`'s `build_claude_messages_payload`).
