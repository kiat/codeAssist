# CodeAssist AI Architecture -- Multi-Bot Implemented for Grading

This document explains how the **LLM Selection** feature extends the existing CodeAssist system.

## 0. Summary
With rapid development of varying LLMs, different models excel on different programming languages and rubric styles. To give users more flexibility and enable them to choose an LLM that they think works best for their assignment, CodeAssist offers a list of LLMs users could choose from and runs the corresponding LLM for feedback. The selected model processes the structured grading tasks and produces rubric-aligned, verifiable feedback.

**Approach**: Dispatch the structured grading task to the user-selected LLM --> Display its response in the UI, with rubric-aligned explanations and evidence, along with suggestions for code accuracy and code efficiency.

## 1. Objectives
- Generate rubric-aligned, verifiable feedback for code submissions.
  - Enable students to understand their scores, based on the rubric as well as the accuracy of their code.
  - Require that feedback explicitly cite rubric items and supporting tool outputs, if possible.
- Provide flexibility in grading feedback by allowing user to select their preferred LLM.
  - Users can choose the model that best suit their language, task, or rubric style.

## 1. Frontend (React)

**What it is**  
The web interface students and instructors use.  

**Changes**  
- Add a **AI Selection Panel**: input box + single-select check box option
- Display feedback along each line of code. If more space is needed, display a response card with feedback.



# TBD (still in the process of understanding)
## 2. Backend (Flask API)


## 3. AI Router / Microservices Layer

## 4. Database (Postgres) 


## Data Flow 