# AGENTS.md

Instructions for AI coding agents (Codex, and any other agentic tool that reads `AGENTS.md`) working in this repository. This file uses plain, tool-agnostic conventions. Claude Code should read `CLAUDE.md` instead (same architecture notes, Claude-specific framing) — the two are kept in sync; update both if the architecture changes.

## Project overview

CodeAssist: Flask + PostgreSQL backend, React frontend, programming-course autograding platform with an AI feedback layer (OpenAI/Gemini/Claude/Ollama). Student code is executed inside Docker containers, both for autograding and to generate context for AI feedback.

- `backend/` — Flask app, blueprints under `routes/`, SQLAlchemy models in `api/models.py`, AI logic in `ai_feedback/`.
- `frontend/` — Create React App, pages under `src/pages/` (role-scoped), shared UI under `src/components/`.
- `docs/ai/` — current, maintained documentation for the AI feedback feature. Read `docs/ai/README.md` before changing anything AI-related; it lists verified gaps between what the code assumes and what actually exists (e.g. no `Assignment.description` column).
- `canvasIntegration/` — standalone scripts syncing grades/roster with Canvas, not part of the Flask app.

## Dev environment

```bash
make install                # backend (pip) + frontend (npm) deps
docker compose up           # postgres, backend, frontend, pgadmin
```
Requires `backend/.env` (`DB_CONNECTION_STRING`, ideally `PASSWORD_SALT`) and `frontend/.env` (`REACT_APP_API_URL`). First-time DB setup (create `codeassist` DB via pgAdmin, then `python3 init_db.py` inside the backend container) is documented in root `README.md`.

After pulling changes with a new Alembic migration:
```bash
docker compose down && docker compose up -d
docker compose exec backend flask db upgrade
```

## Testing instructions

```bash
make test                                              # everything
cd backend && python -m pytest                         # backend, with coverage (pytest.ini default)
cd backend && python -m pytest --no-cov                 # backend, faster
cd backend && python -m pytest test --ignore=test/stress   # skip slow/Docker-heavy stress suite
cd backend && PYTHONPATH=. python -m pytest test/unit/test_code_editor.py -k some_test_name  # one test
cd frontend && npm test -- --watchAll=false             # frontend, once (not watch mode)
```

Notes:
- CI (`.github/workflows/tests.yml`) runs backend pytest with coverage on push/PR to `main`. Frontend tests are **not** currently run in CI — don't assume a green CI run means frontend tests pass.
- `backend/test/unit/` does not require Docker. `backend/test/it/` and `backend/test/stress/` spin up real Docker containers for autograder execution and will fail or hang if Docker isn't running — don't run those in an environment without Docker access.
- Before opening a PR, run the backend unit suite at minimum; run the full suite (`make test`) if you touched Docker-execution or migration code.

## Code conventions specific to this repo

- Every Docker code-execution endpoint (`upload_submission`, `submit_code`, `run_code`, `rerun_submission_autograder`, `test_autograder_submission`, `upload_assignment_autograder`) follows the same pattern: create a detached container, `put_archive` a tar stream of the student code, `docker exec` a script, read results, then stop/remove the container in a `finally`/`except` block. Match this pattern rather than introducing a new execution style.
- AI provider calls live in `ai_feedback/integration.py`, one function per provider (`get_structured_feedback_from_openai/gemini/claude/ollama`). Provider JSON responses are unreliable — always route new provider output through `parse_feedback_json`/`load_feedback_json` rather than calling `json.loads` directly.
- Instructor-controllable data going to the AI must be filtered through `build_allowed_feedback_context()` in `ai_feedback/settings.py` (respects `Assignment.ai_allowed_inputs`). The `/ai_chat` endpoint currently does **not** do this — it's a known, documented gap (`docs/ai/README.md`), not a pattern to copy into new code.
- API keys (course/assignment-level) are stored encrypted via `util/encryption_utils.py` (Fernet, key from `API_SECRET_KEY`). Never log or persist a decrypted key; decrypt only at the point of use.
- Course-level AI settings are the default; assignment-level settings override them only when `Assignment.use_course_ai_default` is `False`. When adding a new AI-related setting, wire it into both the course-default and assignment-override resolution (see `get_provider_and_model`/`get_temperature` in `ai_feedback/integration.py` for the existing pattern).

## PR instructions

- Title format: no enforced convention observed in git history; prefer `<type>: <summary>` (e.g. `fix: ...`, `docs: ...`, `feat: ...`) for consistency with recent commits.
- Keep unrelated file changes out of a PR — this repo's local checkouts can accumulate a large number of incidentally-modified files (line-ending or environment differences); stage explicit paths (`git add <path>`) rather than `git add -A`/`git add .` unless you've verified the full diff is intentional.
- If you touched `ai_feedback/settings.py` or `ai_feedback/integration.py`, update `docs/ai/architecture.md` if the change affects data flow, and update `docs/ai/README.md`'s gap list if it closes (or introduces) one of the documented gaps.
