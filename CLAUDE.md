# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

CodeAssist: a Flask + PostgreSQL backend and React frontend for programming-course autograding, with an AI feedback layer (OpenAI/Gemini/Claude/Ollama) bolted onto the submission pipeline. Student code runs sandboxed in Docker containers, both for autograding and for AI-context generation.

## Commands

### Setup
```bash
make install                # installs backend (pip) + frontend (npm) deps
docker compose up           # starts postgres, backend, frontend, pgadmin
```
Backend needs `backend/.env` with `DB_CONNECTION_STRING` (and ideally `PASSWORD_SALT`); frontend needs `frontend/.env` with `REACT_APP_API_URL`. See root `README.md` for the full first-time setup (creating the `codeassist` DB via pgAdmin, running `init_db.py`).

### Tests
```bash
make test                                   # backend + frontend
cd backend && python -m pytest              # backend only (coverage is on by default via pytest.ini)
cd backend && python -m pytest --no-cov     # backend only, faster, no coverage
cd backend && python -m pytest test --ignore=test/stress   # skip slow/Docker-heavy stress tests
cd backend && PYTHONPATH=. python -m pytest test/unit/test_code_editor.py -k test_name  # single test
cd frontend && npm test -- --watchAll=false                # frontend, run once
cd frontend && npx react-scripts test --watchAll=false --testPathPattern='AIChatPanel'   # single frontend suite
```
CI (`.github/workflows/tests.yml`) only runs backend pytest with coverage — frontend tests are not currently gated in CI. Many backend tests spin up real Docker containers (autograder execution); those live mostly under `test/it/` and `test/stress/` and will fail/hang without Docker running. `test/unit/` is safe to run without Docker.

### Migrations
After pulling a branch with a new migration:
```bash
docker compose down && docker compose up -d
docker compose exec backend flask db upgrade
```
New migrations: `cd backend && flask db migrate -m "..."` then review the generated file in `backend/migrations/versions/` before committing — this project's migration chain has previously needed manual head-merging (see `1bdb41066778_merge_migration_heads.py`), so check `flask db heads` if you hit "multiple heads" errors.

## Architecture

### Backend: app factory + blueprints
`backend/api/__init__.py::create_app()` builds the Flask app, initializes SQLAlchemy/Marshmallow/Migrate/CORS, then calls `routes.register_routes(app)`. Each domain lives in its own blueprint under `backend/routes/`: `user.py`, `course.py`, `assignment.py`, `submission.py`, `code_editor.py`, `ai_feedback.py`, `regrade_request.py`. `backend/app.py` just instantiates the app with `config.Config`; tests use `config.TestConfig`.

### Two submission paths converge on one grading + AI pipeline
Students submit either by uploading a file (`routes/submission.py::upload_submission`) or through the in-browser editor (`routes/code_editor.py::submit_code`). Both: save the code, spin up a Docker container from the assignment's `autograder_image_name`, `docker exec` the autograder, read back `results.json`, write a `Submission` row, then launch `ai_feedback.integration.async_get_ai_feedback` in a background `threading.Thread` to generate AI feedback asynchronously (feedback lands on the submission after the HTTP response has already returned). `routes/code_editor.py::run_code` is a separate, submission-free path — it also runs Docker, but never creates a `Submission` or triggers AI feedback.

### AI feedback is split across two modules by concern
- `ai_feedback/settings.py` — the *policy* layer: prompt normalization/validation, `ai_allowed_inputs` filtering (`build_allowed_feedback_context`), per-student usage-limit enforcement (`check_feedback_limits`), chat history read/write (`ai_chat_messages` table, last-20-message window).
- `ai_feedback/integration.py` — the *mechanism* layer: one function per provider (`get_structured_feedback_from_{openai,gemini,claude,ollama}`), prompt assembly, and defensive JSON parsing (`parse_feedback_json`/`load_feedback_json`) since providers don't reliably return clean JSON.

Submission-triggered feedback (`async_get_ai_feedback`) goes through both modules and respects `ai_allowed_inputs`. The interactive `/ai_chat` endpoint in `routes/code_editor.py` builds its own context inline instead of reusing `build_allowed_feedback_context` — this is a known inconsistency, not an oversight to "fix" casually; see `docs/ai/README.md` before touching either code path.

Full current-state writeup, including known gaps (no `Assignment.description` column despite code assuming one exists, `.zip` uploads breaking AI feedback text-reading, `student.coding_insights` being overwritten rather than accumulated): **`docs/ai/README.md`** and **`docs/ai/architecture.md`**. Read those before making AI-feedback-related changes — they document real, verified gaps in the shipped behavior, not aspirational docs.

### Course → Assignment settings inheritance
AI provider/model/temperature/style can be set at the course level (`Course.default_ai_provider` etc.) or overridden per assignment (`Assignment.use_course_ai_default=False` + `ai_feedback_provider` etc.). `ai_feedback/integration.py::get_provider_and_model`/`get_temperature`/`get_provider_credentials` implement the fallback resolution — always assignment-override-if-set, else course default. API keys are stored encrypted (`util/encryption_utils.py`, Fernet, key from `API_SECRET_KEY`/`init_encryption_keys.py`) and decrypted only at request time.

### Docker sandboxing pattern
Every code-execution path (`upload_submission`, `submit_code`, `run_code`, `rerun_submission_autograder`, `test_autograder_submission`, `upload_assignment_autograder`) follows the same shape: create a detached container from an image, `put_archive` the student code in as a tar stream, `docker exec` a script, read results, then `container.stop()`/`container.remove()` in a `finally`/`except` block. When adding a new code-execution endpoint, follow this existing pattern rather than inventing a new one — cleanup-on-all-exit-paths is easy to get wrong here (several existing endpoints have slightly different but deliberate variations, e.g. `run_code` uses a default `python:3.11-slim` image when no autograder is configured).

### Frontend structure
React app under `frontend/src/`, pages under `pages/` (role-scoped: `instructor/`, `admin/`, `student/`), reusable pieces under `components/`. The code editor page (`pages/codeEditor/index.js`) composes `CodeEditor.js` (CodeMirror 6) and `AIChatPanel.js` side by side; `AIFeedbackSettingsSection.js` is the reusable instructor-side AI config block shared between `CreateAssignment.js` and `pages/assignmentSettings/index.js`. See `docs/ai/code-editor-feedback.md` for the editor's data flow.

### Docs
`docs/ai/` is the maintained, current source of truth for the AI feedback feature (start at `docs/ai/README.md`). `docs/endpoints/` documents non-AI REST endpoints. `docs/ai/design-history/` and `docs/ai/proposals/` contain historical/unimplemented designs — do not treat their content as describing current behavior.
