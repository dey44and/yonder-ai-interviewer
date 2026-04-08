# Yonder AI Interviewer

This repository contains a proof-of-concept AI interviewer designed to explore how artificial intelligence affects a person's work and daily life. The solution supports both a command-line communication, and a lightweight web experience, while keeping the interview flow structured.

The main design goal was to build a small but coherent system that demonstrates:

- a clear separation between transport layers and interview logic
- structured LLM output instead of free-form text
- lightweight persistence for both chat history and agent state (for web version).
- a simple path from local development to containerized execution

## Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Architecture Overview](#architecture-overview)
- [Core Design Decisions](#core-design-decisions)
- [Application Flow](#application-flow)
- [Project Structure](#project-structure)
- [Running Locally](#running-locally)
- [Docker](#docker)
- [Testing and CI](#testing-and-ci)
- [Current Limitations](#current-limitations)
- [Possible Improvements](#possible-improvements)

## Project Overview

The interviewer is centered around a short, topic-guided conversation. The user chooses a topic such as `AI in the workplace` or `Scientific research`, and the agent conducts a short interview that aims to understand:

- the interviewee's role or professional context
- how AI currently appears in their work or daily routines
- the benefits, risks, and trade-offs they perceive
- a short final summary and a few keywords that can be extracted from discussion.

The application currently exposes two interfaces:

- a CLI application for quick testing
- a FastAPI-based web application with a small browser UI

## Key Features

- Structured LLM responses via a dedicated `ResponseFormat` schema
- Topic-based interview initialization
- Explicit interview lifecycle with completion tracking
- Transcript persistence for the web app using SQLite
- Agent checkpoint persistence using LangGraph's SQLite checkpointer
- Final summary and keyword generation
- Automated tests and GitHub Actions CI
- Docker-based execution for both the CLI and web variants

## Architecture Overview

At a high level, the application is split into four layers:

### 1. Entry Points

- `cli_app.py` starts the command-line interview flow
- `chat_app.py` starts the FastAPI application

### 2. Controllers

- `CLIInterviewController` handles terminal interaction
- `WebInterviewController` handles state transitions for the web interview

The controller layer is responsible for:

- deciding how the interview starts
- deciding how each user turn is processed
- determining when the interview is complete
- formatting the final response for the interface that requested it

### 3. Services

- `AgentService` contains the LLM agent and checkpointing logic
- `TranscriptService` stores transcript entries and exports them to JSON
- `Database` persists web chat messages in SQLite

This keeps the transport-specific logic separate from persistence and model orchestration.

### 4. Models and Prompting

- `ResponseFormat` defines the structured output expected from the agent
- `ChatMessage` defines the message contract used by the browser UI
- `SYSTEM_PROMPT` defines the interview objective, flow, privacy rules, and output rules

## Core Design Decisions

### Structured Output Instead of Free-Form Text

The agent is configured to return a `ResponseFormat` object instead of arbitrary text. This makes the application more predictable because the caller can rely on explicit fields as follows:

- `response`
- `question_type`
- `question_number`
- `interview_complete`
- `summary`
- `keywords`

This is especially useful for deciding when the interview should stop and what the final UI message should contain.

### Separate CLI and Web Controllers

The CLI and web flows share the same interview intent, but they have different responsibilities:

- the CLI version manages I/O operations through `print()` and `input()`
- the web version manages session lifecycle and UI-friendly message payloads

### State Machine for the Web Flow

The web controller uses a small explicit state machine:

- `NOT_STARTED`
- `ACTIVE`
- `COMPLETED`

This keeps the interview lifecycle easy to reason about and prevents invalid transitions such as continuing the conversation after completion.

### SQLite for Lightweight Persistence

The project uses SQLite in two different ways:

- one database for persisted web chat history
- one database for LangGraph agent checkpoints

This was a specific trade-off for a POC: SQLite is easy to run locally, works well in Docker, and avoids introducing a heavier external service too early.

### Simple Frontend on Purpose

The browser UI uses FastAPI plus a small TypeScript file served directly by the backend. This keeps the web layer lightweight and easy to inspect while still demonstrating:

- topic selection
- session-based chat
- streaming of user and model messages
- interview completion handling

For an interview task, this keeps the focus on architecture and backend reasoning rather than frontend complexity.

## Application Flow

### CLI Flow

1. The user starts `cli_app.py`.
2. The CLI controller asks the user to choose a topic.
3. The topic is turned into an initialization message for the agent.
4. The agent asks questions until `interview_complete=True`.
5. The transcript is exported to `results/`.

### Web Flow

1. The user opens the FastAPI app.
2. The frontend sends `POST /interview/start` with the selected topic.
3. A `WebInterviewController` is created and assigned a session id.
4. The first agent question is returned and stored in SQLite.
5. Each answer is sent to `POST /interview/{session_id}/message`.
6. The backend streams the user message and then the model message back to the frontend.
7. When the interview completes, the final message includes the closing text, summary, and keywords.

### Persistence Flow

- The web transcript is stored in SQLite through `persistence/database.py`.
- The agent's conversation state is stored through LangGraph's SQLite checkpointer.
- Transcripts are also exported as JSON files in `results/` at the end of an interview.

## Project Structure

```text
.
├── chat_app.py                    # FastAPI entrypoint
├── cli_app.py                     # CLI entrypoint
├── controllers/
│   ├── cli_interview_controller.py
│   └── web_interview_controller.py
├── services/
│   ├── agent_service.py
│   └── transcript_service.py
├── persistence/
│   └── database.py
├── models/
│   └── model.py
├── static/
│   └── chat_app.ts
├── templates/
│   └── chat_app.html
├── tests/
│   ├── test_chat_app.py
│   ├── test_database.py
│   └── test_web_interview_controller.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Running Locally

### Prerequisites

- Python 3.11
- an OpenAI API key exposed as `OPENAI_API_KEY`

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the web app:

```bash
python chat_app.py
```

Run the CLI app:

```bash
python cli_app.py
```

## Docker

Set `OPENAI_API_KEY` in a local `.env` file, then build and run with Docker Compose.

Build the image:

```bash
docker compose build
```

Start the web app:

```bash
docker compose up web
```

Run the CLI app:

```bash
docker compose run --rm cli
```

Persistent app data is stored in:

- `./data` for SQLite databases
- `./results` for exported transcripts

## Testing and CI

The repository includes focused pytest coverage for the most important flows:

- database behavior
- web controller state transitions
- FastAPI interview endpoints

CI is configured with GitHub Actions and currently runs:

- dependency installation
- `flake8`
- `black --check`
- `pytest`

This provides a lightweight but useful feedback loop for a POC repository.

## Current Limitations

- Active web sessions are stored in an in-memory `sessions` dictionary, so the controller object itself is not automatically reinitialized after a process restart.
- The frontend is intentionally simple and does not use a modern build system.
- The Docker image is heavier than ideal because runtime and development dependencies are still grouped together in `requirements.txt`.
- Some persistence behavior is designed for local/demo use rather than multi-instance deployment.

## Possible Improvements

- Split runtime and development dependencies into separate requirement files
- Replace in-memory session tracking with fully persistent session restoration
- Add authentication and per-user session
- Introduce a richer frontend build pipeline if the project grows beyond POC scope
- Add more end-to-end tests around the full interview lifecycle
