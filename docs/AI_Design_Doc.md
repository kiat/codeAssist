# CodeAssist AI Architecture -- Multi-Bot Implemented for Grading

This document explains how the **Multiple-LLM** feature extends the existing CodeAssist system.

## 0. Summary
With rapid development of varying LLMs, different models excel on different languagesand rubric styles. To deliver reliable, explainable, and low-latency. grading with provenance, CodeAssist sends the same structued grading task to an ensemble of LLMs, chosen by the user, in parellel. Each model's response is validated against a schema, cross-checked with deterministic tool results (unit tests), and cited back to rubric items.
**Approach**: Fire the same structured grading task to multiple LLMs concurrently, based on user choice → Display each and all respons in the UI (per-model tabs for transparency), TBD.

## 1. Objectives
- Generate rubric-aligned, verifiable feedback for a code submission.
  - Enable students to understand their scores, based on the rubric as well as the accuracy of their code.
  - Every piece of feedback must explicityl cite rubric items and tool evidence.
- Support optional multi-LLM orchestration for more robust feedback.
  - Through multi-LLM orchestration, mitigates randomness and captures diverse strengths.

## 1. Frontend (React)

**What it is**  
The web interface students and instructors use.  

**Changes**  
- Add a **Multi-AI Feedback Panel**: input box + bot selection (checkboxes, users would choose all that they hope to apply)
- Display **side-by-side response cards** of results from the selected models. TBD

**Why it matters**  
Without this, users can’t interact with multiple AIs or compare outputs.



# TBD (still in the process of understanding)
## 2. Backend (Flask API)


## 3. AI Router / Microservices Layer

## 4. Database (Postgres) 


## Data Flow 