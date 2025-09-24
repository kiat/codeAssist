<img width="1024" height="768" alt="image" src="https://github.com/user-attachments/assets/d4c323d0-ac6f-454d-82ef-2859bd83fdbe" />

 # ChatALL Integration into CodeAssist

This document explains how the **Multi-AI Chat (ChatALL)** feature extends the existing CodeAssist system.


## 1. Frontend (React)

**What it is**  
The web interface students and instructors use.  

**Changes**  
- Add a **Multi-AI Chat Panel**: input box + bot selection.  
- Display **side-by-side response cards** from GPT, Claude, Gemini, Local LLM.  

**Why it matters**  
Without this, users can’t interact with multiple AIs or compare outputs.


## 2. Backend (Flask API)

**What it is**  
The gateway between the frontend and all services.  

**Changes**  
- Add endpoint:  
  ```http
  POST /api/multi-ai-chat

Backend returns JSON → Frontend renders side-by-side cards.

Optionally, results are stored in Database.

## 3. AI Router / Microservices Layer

**What it is**  
The engine that communicates with AI models.

**Options**  
- **Single Router Service**: one container that fans out requests.  
- **Multiple Services**: separate container per model.  

**Supported Models**  
- GPT (OpenAI)  
- Claude (Anthropic)  
- Gemini (Google)  
- Local LLM (Ollama / HuggingFace models)  

**Why it matters**  
The router prevents the frontend from hitting multiple APIs directly and ensures **parallel calls + aggregation**.

## 4. Database (Postgres) 

**What it is**  
Persistence layer for prompts, responses, and preferences.

**Schema Additions**  
- `prompts (id, user_id, text, timestamp)`  
- `responses (id, prompt_id, bot, response, highlights)`  
- `preferences (enabled_bots, dark_mode, etc.)`  

**Why it matters**  
- Save/reload chat history.  
- Enable analytics (e.g., which AI gives best results).  
- Give instructors control (enable/disable AI feedback).


## Data Flow 

1. Student enters a **prompt** in the frontend.  
2. Backend (`/api/multi-ai-chat`) receives it.  
3. AI Router fans out to GPT / Claude / Gemini / Local LLM.  
4. Router aggregates results → sends them back to backend.  
5. Backend returns JSON → **frontend renders responses side by side**.  
6. *(Optional)* Responses are saved in **Postgres** for history/analytics.

reference :
https://github.com/ai-shifu/ChatALL


