# AI Feedback Architecture

## Overview

CodeAssist provides personalized, AI-powered feedback to students on their programming submissions. The system integrates with multiple LLM providers (OpenAI, Gemini, Claude) and supports both automated submission-level feedback and interactive student-AI chat.

## Key Features

- **Assignment-Level AI Configuration** — Instructors configure prompts, allowed inputs, usage limits, and wait times per assignment
- **Student Prompt Selection** — Students choose from instructor-configured feedback prompts
- **Student AI Memory** — The system remembers prior conversations and coding patterns per student
- **Reference Solution Comparison** — AI compares student code against an optimal approach
- **Per-Student Usage Limits** — Max requests and cooldown periods enforced server-side
- **Input Permission Control** — Instructors control which data (code, test results, description) the AI can access

## Architecture

### Data Flow

```
Student Code Editor → AI Chat Panel → Backend /ai_chat
    ↓
1. Verify student + enrollment
2. Check feedback limits (max_requests, wait_seconds)
3. Fetch enabled prompt by prompt_id
4. Load student coding_insights from User table
5. Load chat history from ai_chat_messages table
6. Build system prompt with student history + assignment context
7. Build user prompt with code + instructor prompt instruction
8. Call LLM provider (OpenAI/Gemini/Claude)
9. Store conversation in ai_chat_messages
10. Record request in ai_feedback_requests
11. Return reply + updated feedback_status
```

### Database Tables

| Table | Purpose |
|-------|---------|
| `users` | `coding_insights` field stores accumulated student patterns |
| `assignments` | AI settings: prompts, allowed inputs, limits, provider/model |
| `ai_feedback_requests` | Per-student request tracking for limit enforcement |
| `ai_chat_messages` | Student-AI conversation history for AI memory |

### Backend Modules

| Module | Responsibility |
|--------|---------------|
| `ai_feedback/settings.py` | Prompt normalization, limit enforcement, chat history, request tracking |
| `ai_feedback/integration.py` | LLM provider calls, prompt building, feedback parsing |
| `routes/code_editor.py` | Student-facing endpoints: `/ai_chat`, `/ai_feedback_status` |
| `routes/ai_feedback.py` | Instructor + student settings endpoints |

### Frontend Components

| Component | Role |
|-----------|------|
| `AIChatPanel.js` | Student chat interface with prompt buttons, remaining count, countdown |
| `AIFeedbackSettingsSection.js` | Instructor prompt/input/limit configuration UI |
| `codeEditor/index.js` | Code editor page integrating AIChatPanel |

## Student AI Memory

### How It Works

1. **Conversation History** — Every user/assistant message is stored in `ai_chat_messages`
2. **Coding Insights** — The `users.coding_insights` field accumulates patterns across submissions
3. **Context Window** — Last 10 chat messages + coding insights are included in each AI request
4. **Personalization** — The AI uses this history to tailor feedback to the student's specific needs

### Storage

- Chat messages are stored with `student_id`, `assignment_id`, `role`, `content`, and `prompt_id`
- Messages are stored concisely (user's text only, not full code dumps) to avoid bloat
- Storage failures are logged but don't break the chat response

## Reference Solution Comparison

### How It Works

When a student selects the "Compare to optimal solution" prompt:

1. The AI receives the assignment description
2. It generates an optimal approach internally
3. It compares the student's code against this approach
4. It provides feedback on algorithmic differences without revealing the full solution

### Prompt Design

The prompt instructs the AI to:
- Analyze the assignment description first
- Generate an optimal approach internally
- Compare time/space complexity
- Identify structural improvements
- Give feedback without copy-paste fixes

## Usage Limits

### Configuration

| Setting | Description |
|---------|-------------|
| `ai_feedback_max_requests` | Max requests per student per assignment (null=unlimited, 0=disabled) |
| `ai_feedback_wait_seconds` | Cooldown between requests (0=no wait) |

### Enforcement

- Server-side: `check_feedback_limits()` in `settings.py` validates before each request
- Client-side: AIChatPanel disables buttons and shows countdown during cooldown
- Response includes updated `feedback_status` with remaining count and wait time

## Input Permissions

Instructors control what data the AI can access:

| Permission | Default | Description |
|-----------|---------|-------------|
| `assignment_description` | ✅ | Assignment text/description |
| `student_code` | ✅ | Student's submitted code |
| `test_results` | ✅ | Autograder test results |
| `test_cases` | ❌ | Test case inputs/expected outputs |
| `student_output` | ✅ | Student's stdout/stderr output |

## API Endpoints

### Student-Facing

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/ai_chat` | POST | Send message to AI, returns reply + feedback_status |
| `/ai_feedback_status` | GET | Get remaining requests and wait time |
| `/assignments/<id>/prompts` | GET | Get enabled prompts for an assignment |

### Instructor-Facing

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/assignments/<id>/ai-settings` | GET | Get full AI settings |
| `/assignments/<id>/ai-settings` | PUT | Update AI settings |

## Default Prompts

1. **Check correctness** — Verify submission against requirements
2. **Debug failed tests** — Analyze test failures
3. **Review edge cases** — Check boundary conditions
4. **Explain runtime errors** — Explain exceptions
5. **Review code style** — Code organization feedback
6. **Suggest algorithmic improvements** — Complexity concerns
7. **Check code syntax** — Syntax and best practices
8. **Compare to optimal solution** — Reference solution comparison
9. **Personalized feedback** — History-aware personalized guidance

## Migration Files

| Migration | Creates |
|-----------|---------|
| `a2b3c4d5e6f7` | `ai_feedback_requests` table |
| `b3c4d5e6f7a8` | `ai_chat_messages` table |

## Testing

### Backend
```bash
cd backend && PYTHONPATH=. python -m pytest test/unit/ --no-cov
```

### Frontend
```bash
cd frontend && npx react-scripts test --watchAll=false --testPathPattern='AIChatPanel'
```
