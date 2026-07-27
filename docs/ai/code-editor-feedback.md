# Code Editor + Student-Facing AI Feedback

> Moved from `docs/code_editor.md` into the AI docs folder, since this is the student-facing side of the AI feature: where AI feedback and AI chat actually surface for a student, alongside the file-upload path. General editor mechanics (autosave, version history) are included since they share the same page and backend routes.

## Overview

The Code Editor feature lets students write, run, and submit Python code directly in the browser, as an alternative to uploading a file. It includes an inline editor (CodeMirror 6), the AI chat panel, version history with auto-save, and a Run button for output/test results.

Students get AI feedback on their work through **two different surfaces**, both backed by the same `ai_feedback/integration.py` pipeline described in `architecture.md`:

- **Submission feedback** — after `/submit_code` (code editor) or `/upload_submission` (file upload) finishes autograding, `async_get_ai_feedback` runs in the background and writes structured JSON feedback (`insights` + line `annotations`) onto the submission, shown on the results page.
- **AI chat** — only available in the code editor (there's no chat UI for uploaded files). Interactive, turn-by-turn, with memory of the last 20 messages (see `architecture.md`).

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (React)                       │
│                                                          │
│  ┌─────────────────────┐  ┌────────────────────────────┐ │
│  │   CodeEditor (left)  │  │   AIChatPanel (right)      │ │
│  │   - CodeMirror 6     │  │   - AI chat, memory-aware  │ │
│  │   - Auto-save (30s)  │  │   - Code review & hints    │ │
│  │   - Run / Submit     │  │                            │ │
│  └──────────┬──────────┘  └────────────┬───────────────┘ │
│             │                           │                 │
│  ┌──────────▼───────────────────────────▼───────────────┐ │
│  │              VersionHistoryModal                      │ │
│  │              (manual saves + latest auto-save)        │ │
│  └──────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────┘
                           │ HTTP API
┌──────────────────────────▼───────────────────────────────┐
│                    Backend (Flask)                        │
│                                                          │
│  /save_code_draft    — Save a draft (auto or manual)     │
│  /get_code_drafts    — List drafts (condensed option)    │
│  /get_latest_draft   — Fetch most recent draft           │
│  /run_code           — Execute code, return output       │
│  /submit_code        — Submit for grading + AI feedback  │
│  /ai_chat            — Chat with AI about current code   │
└──────────────────────────────────────────────────────────┘
```

## Key Components

| Component | Role |
|---|---|
| `frontend/src/pages/codeEditor/index.js` | Page at `/codeEditor/:assignmentId`; left panel editor, right panel AI chat; auto-saves every 30s |
| `frontend/src/components/CodeEditor.js` | CodeMirror 6 wrapper, toolbar (Save/Submit/Run/Feedback/History), save-status indicator |
| `frontend/src/components/AIChatPanel.js` | Chat UI; sends student code + message to `/ai_chat`; system prompt pushes hints over full solutions |
| `frontend/src/components/VersionHistoryModal.js` | Save history browsing/restore |
| `backend/routes/code_editor.py` | All routes below, Docker-sandboxed execution |

## How the Run Button Works

1. Student clicks **Run** → frontend sends `{ student_id, assignment_id, content, file_name }` to `POST /run_code`.
2. Backend validates the assignment exists, is published, and checks due dates.
3. **With autograder configured:** runs student code in the autograder Docker image, captures stdout/stderr, also runs `run_autograder` for test results. Returns `{ output, stdout, stderr, passed, score, tests[] }`.
4. **Without autograder:** runs in a default `python:3.11-slim` container, stdout/stderr only, `passed` based on exit code, `score: 0`, `tests: []`.
5. Run does **not** create a submission or trigger AI feedback — only `/submit_code` and `/upload_submission` do that.

## How Auto-Save Works

- `setInterval`, 30s, only fires if code changed since the last save.
- Save status: `idle` → `saving` → `saved` → `idle` (after 3s).
- Ctrl+S / Cmd+S triggers an immediate manual save.

## How Submit Works (triggers AI feedback)

1. Student clicks **Submit** → confirmation dialog → `POST /submit_code` with `{ student_id, assignment_id, content, file_name }`.
2. Backend checks due dates/extensions.
3. If autograder exists: runs in Docker, saves submission with results, **then launches `async_get_ai_feedback` in a background thread**.
4. If no autograder: saves the submission directly (AI feedback is still attempted if `ai_feedback_enabled`).
5. A final (non-auto-saved) draft snapshot is recorded for version history.
6. Student is redirected to the results page, where feedback appears once the background job finishes (may not be instant).

## Assignment Configuration (Instructor)

In `CreateAssignment.js`:

| Setting | Description |
|---|---|
| **Enable Code Editor** | Allows students to write code in-browser (`allow_file_upload` and `enable_code_editor` — at least one must stay on) |
| **Configure Autograder** | Enables Docker-based execution for Run and Submit |
| **Enable AI Feedback** | Enables both submission feedback generation and the AI chat panel |

An assignment can have the code editor enabled with no autograder — students can write/save/run code (against a default Python image, no test results) but won't get scored test results until an autograder is configured.

## Data Model — CodeDraft

| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `student_id` | UUID (FK → users) | Owner |
| `assignment_id` | UUID (FK → assignments) | Assignment |
| `content` | TEXT | Code content |
| `file_name` | VARCHAR | e.g. `solution.py` |
| `version_number` | INT | Incrementing per student/assignment |
| `saved_at` | TIMESTAMP | |
| `auto_saved` | BOOLEAN | True if auto-save, False if manual/submit snapshot |

## Manual QA Checklist

**Prerequisites:** Docker running; a course with an assignment that has `enable_code_editor: true`; an autograder image configured if testing scored Run results.

- **Page load** — editor loads with default comment, latest draft restored, AI Chat panel visible.
- **Auto-save** — type code, wait 30s, see Saving→Saved, refresh, confirm code persists.
- **Manual save (Ctrl+S)** — Saving→Saved indicator, new entry in version history.
- **Run, no autograder** — `print("Hello, world!")` → output panel shows it, green pass indicator.
- **Run, with autograder** — output panel shows stdout/stderr + a test results table.
- **Run, error case** — `def foo(` → error shown, red fail indicator.
- **Submit** — confirmation dialog → redirect to results page with submission ID in URL.
- **AI chat** — ask "Can you explain what this code does?" → AI responds with a hint-style explanation, **not** the complete solution.
- **AI chat memory** — send a follow-up referencing the previous message, confirm the AI's reply shows it has context (tests this in code: `get_chat_history(limit=20)`).
- **Version history** — make several manual saves with different code, open History, restore an older version, confirm content matches.
- **File-upload parity check**
  - Upload a `.py` file and confirm AI feedback appears.
  - Upload a ZIP file containing source files and confirm AI feedback is generated.
  - Upload an invalid ZIP and confirm a clear extraction error is shown.
