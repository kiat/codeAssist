> **Proposal, not implemented.** This reflects Kia Teymourian's latest AI
> feedback direction from August 2026: keep student AI interaction controlled,
> assignment-level, and focused on instructor-approved learning goals rather
> than free-form chat.

# AI Submission-Defense Questions

## Goal

After a student's submission passes the static test cases, an AI agent generates
one or more targeted understanding questions about the submitted code. The
student answers in writing, or eventually by recorded audio, to explain their
own implementation choices.

This is meant to check code understanding without asking the AI for direct
answers. It fits the controlled-feedback direction better than a free-form chat
box.

## Example Flow

1. Student submits code.
2. Autograder/static tests pass.
3. Backend extracts the submitted source and test context already used by AI
   feedback.
4. AI generates a short, line-specific question.
5. Student answers in text, or records an audio explanation in a later version.
6. Instructor can review the question/answer pair alongside the submission.

## Example Questions

```text
Line 142 uses a for loop over every item in the list. What task is this loop
performing, and why is a linear scan appropriate here?
```

```text
Your helper function updates `seen` before checking the next value. What
invariant is `seen` supposed to maintain at that point in the algorithm?
```

```text
This branch handles the empty-input case before the main loop starts. What
failure would occur if that branch were removed?
```

```text
Your code converts the input string to lowercase before comparing values. What
kind of test case would fail if that normalization step were skipped?
```

## Suggested Data Model

This needs a new table rather than overloading `ai_chat_messages`, because these
question/answer records are tied to a specific submitted artifact and may be
graded or reviewed later.

Possible table:

```text
submission_defense_questions
- id
- submission_id
- assignment_id
- student_id
- question_text
- source_line_start
- source_line_end
- student_text_answer
- student_audio_path or student_audio_blob metadata
- ai_evaluation_json nullable
- created_at
- answered_at nullable
```

## Assignment-Level Controls

The feature should be configured per assignment:

- enabled / disabled
- number of questions
- when to ask questions, e.g. after static tests pass only
- allowed question focus areas, e.g. loops, edge cases, data structures,
  helper functions, failed/near-miss tests
- whether audio answers are allowed or required

Do not put these controls at the course default level unless product direction
changes; instructors asked for assignment-level flexibility.

## Implementation Notes

- Reuse `ai_feedback/source_extraction.py` for source text.
- Reuse `build_allowed_feedback_context()` so instructor input permissions still
  apply.
- Avoid sending hidden/private test details unless the assignment allows that
  input category.
- Generate questions after the autograder result is available, not before.
- Keep the student response UI separate from the current prompt panel so it is
  clear this is an assessment/explanation step, not open chat.

## Open Questions

- Should answers be required before the submission is considered complete, or
  optional for instructor review?
- Should audio be stored in the app database, object storage, or not stored at
  all after transcription?
- Should the AI evaluate the student's explanation automatically, or only
  generate the question and leave evaluation to instructors?
- Should students see AI feedback before or after answering the defense
  question?
