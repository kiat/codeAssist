# Code Editor Feature

## Overview

The Code Editor feature allows students to write, run, and submit Python code directly in the browser without uploading files. It includes an inline code editor (CodeMirror 6), AI-powered feedback, version history with auto-save, and a Run button that shows program output and test results.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (React)                       │
│                                                          │
│  ┌─────────────────────┐  ┌────────────────────────────┐ │
│  │   CodeEditor (left)  │  │   AIChatPanel (right)      │ │
│  │   - CodeMirror 6     │  │   - GPT-powered assistant  │ │
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

### 1. Code Editor Page (`frontend/src/pages/codeEditor/index.js`)
- Main page for inline code editing
- Route: `/codeEditor/:assignmentId`
- Left panel: CodeMirror editor with toolbar (Save, Submit, Run, Feedback, History)
- Right panel: AI Chat for conversing with the AI assistant
- Auto-saves code every 30 seconds via `setInterval`

### 2. CodeEditor Component (`frontend/src/components/CodeEditor.js`)
- Wraps CodeMirror 6 with line numbers, syntax highlighting
- Toolbar with Save, Submit, Run, Request Feedback, Version History buttons
- Auto-save status indicator: `idle` → `saving` → `saved` → `idle`

### 3. AIChatPanel (`frontend/src/components/AIChatPanel.js`)
- Chat interface for AI-powered code assistance
- Sends student code + message to the backend AI endpoint
- System prompt encourages hints and guiding questions (no complete solutions)

### 4. VersionHistoryModal (`frontend/src/components/VersionHistoryModal.js`)
- Displays save history (manual saves + latest auto-save when condensed)
- Allows restoring a previous version

### 5. Backend Routes (`backend/routes/code_editor.py`)
- All routes under the `code_editor` Flask blueprint
- Uses Docker containers for sandboxed code execution

## How the Run Button Works

### Flow
1. Student clicks **Run** in the editor toolbar
2. Frontend sends `{ student_id, assignment_id, content, file_name }` to `POST /run_code`
3. Backend validates the assignment exists, is published, and checks due dates

### With Autograder Configured
1. Runs student code in the autograder Docker container
2. Captures stdout/stderr from `python solution.py`
3. Also runs the autograder's `run_autograder` script for test results
4. Returns: `{ output, stdout, stderr, passed, score, tests[] }`

### Without Autograder
1. Runs student code in a default `python:3.11-slim` Docker container
2. Captures stdout/stderr only (no test results)
3. Returns: `{ output, stdout, stderr, passed (based on exit code), score: 0, tests: [] }`

### Response Format
```json
{
  "output": "Hello, world!\n",
  "programOutput": "Hello, world!\n",
  "stdout": "Hello, world!\n",
  "stderr": "",
  "passed": true,
  "score": 0,
  "tests": []
}
```

### Frontend Output Panel
- Always displays the program output after clicking Run
- Shows pass/fail status with color-coded indicators (✓ green / ✗ red)
- If test results exist, displays a test summary table with individual pass/fail and scores
- Shows a "Running code…" spinner while execution is in progress

## How Auto-Save Works

- Uses `setInterval` with a 30-second interval
- Only saves if code has changed (`codeRef.current !== lastSavedCodeRef.current`)
- Tracks save status: `idle` → `saving` → `saved` → `idle` (after 3s)
- Visual indicator in toolbar shows current save state
- Ctrl+S (or Cmd+S on Mac) triggers an immediate manual save

## How Submit Works

1. Student clicks **Submit** in the toolbar
2. Confirmation dialog appears
3. Frontend sends `{ student_id, assignment_id, content, file_name }` to `POST /submit_code`
4. Backend checks due dates and extensions
5. If autograder exists: runs in Docker, saves submission with results
6. If no autograder: saves submission directly
7. A final draft snapshot is saved for version history
8. Student is redirected to the results page

## Assignment Configuration (Instructor)

In the assignment creation form (`CreateAssignment.js`):

| Setting | Description |
|---------|-------------|
| **Enable Code Editor** | Toggle Switch — allows students to write code in the browser |
| **Configure Autograder** | Toggle Switch — enables Docker-based code execution for Run and Submit |
| **Enable AI Feedback** | Toggle Switch — enables the AI chat assistant |

- An assignment **can** be created with just the code editor enabled (no autograder)
- In that case, students can write and save code, but the **Run** button will execute against a default Python Docker image (no custom test results)
- To get test results from the Run button, the instructor must configure an autograder

## Data Model

### CodeDraft Table
| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `student_id` | UUID (FK → users) | Student who owns the draft |
| `assignment_id` | UUID (FK → assignments) | Assignment this draft belongs to |
| `content` | TEXT | The code content |
| `file_name` | VARCHAR | Filename (e.g. `solution.py`) |
| `version_number` | INT | Incrementing version number per student/assignment |
| `saved_at` | TIMESTAMP | When the draft was saved |
| `auto_saved` | BOOLEAN | True if auto-saved, False if manually saved |

## Test Steps (Manual QA)

### Prerequisites
1. Docker must be running (for code execution)
2. A course with an assignment that has `enable_code_editor: true`
3. If testing Run with autograder results: configure an autograder Docker image on the assignment

### Test: Code Editor Page Load
1. Log in as a student enrolled in the course
2. Navigate to the assignment and click "Open Code Editor"
3. Verify: Editor loads with a default `# Write your solution here` comment
4. Verify: Latest draft is loaded (if one exists)
5. Verify: AI Chat panel is visible on the right

### Test: Auto-Save
1. Type some code in the editor
2. Wait 30 seconds
3. Verify: "Saving..." indicator appears, then "Saved"
4. Refresh the page
5. Verify: Previously typed code is restored

### Test: Manual Save (Ctrl+S)
1. Type some code
2. Press Ctrl+S (or Cmd+S on Mac)
3. Verify: "Saving..." → "Saved" indicator
4. Check version history — should show a new manual save entry

### Test: Run Button (Without Autograder)
1. Type `print("Hello, world!")` in the editor
2. Click the **Run** button
3. Verify: "Running code…" spinner appears
4. Verify: Output panel appears below the editor showing `Hello, world!`
5. Verify: Pass status is shown (green ✓ for exit code 0)

### Test: Run Button (With Autograder)
1. Type code in the editor
2. Click **Run**
3. Verify: Output panel shows program stdout/stderr
4. Verify: Test results section shows individual test pass/fail with scores

### Test: Run Button (Error Output)
1. Type code with a syntax error: `def foo(`
2. Click **Run**
3. Verify: Output panel shows the error message
4. Verify: Status shows ✗ Failed

### Test: Submit Code
1. Write valid code
2. Click **Submit**
3. Verify: Confirmation dialog appears
4. Click "Submit" in the dialog
5. Verify: Navigates to the results page with submission ID in the URL

### Test: AI Chat
1. Click in the AI Chat input field
2. Type "Can you explain what this code does?"
3. Verify: AI responds with a helpful message
4. Verify: AI does NOT provide the complete solution (only hints/guidance)

### Test: Version History
1. Make several manual saves (Ctrl+S) with different code
2. Click the **History** button
3. Verify: Modal shows a list of saved versions
4. Click on an older version
5. Verify: Editor content is restored to that version
