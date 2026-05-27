# English Helper Bot

**English Helper Bot** is a Telegram bot for guided English practice. It helps learners choose a level and module, complete interactive tasks step by step, receive automatic feedback, and track their progress.

Try the bot in Telegram: **https://t.me/engleohelperbot**

<p align="center">
  <img src="docs/screenshots/logo-removebg-preview.png" alt="English Helper Bot logo" width="220"/>
</p>

## Product Idea

The bot is designed as a lightweight learning assistant for English practice outside the classroom. Instead of sending students long worksheets, it turns exercises into a conversational Telegram flow:

- choose a course library
- select a module such as Grammar, Vocabulary, Reading, or Speaking
- open tasks grouped by textbook-style units
- answer questions one by one
- get a score and feedback
- return to progress and continue later

The goal is to make homework and revision easier to start, easier to check, and easier to continue.

## Screenshots

<p align="center">
  <img src="docs/screenshots/bot_1.jpg" alt="Bot navigation and task selection" width="420"/>
</p>

<p align="center">
  <img src="docs/screenshots/bot_2.jpg" alt="Task execution and feedback" width="420"/>
</p>

## Key Features

- Telegram-first learning flow
- Course libraries with levels, modules, units, and tasks
- Step-by-step task sessions
- Automatic scoring with rule-based checks
- LLM-compatible scoring adapter for richer feedback
- Progress tracking by user, library, module, and task
- JSON-based content format for adding new exercises
- Clean callback navigation with Back, Retry, Next task, and Progress flows

## Tech Stack

- Python
- aiogram
- Pydantic-style domain models
- JSON task libraries
- File-based state and event storage
- Optional OpenAI-compatible LLM scoring endpoint
- uv for local dependency management

## Architecture

The project is split into clear layers:

- `src/app` - configuration, dependency wiring, startup
- `src/bot` - Telegram router, handlers, middleware, keyboards, renderers
- `src/core` - domain models and services for sessions, scoring, and progress
- `src/infra` - storage, task-library loading, and scoring adapters
- `src/libraries` - JSON task libraries used by the bot

This structure keeps the learning engine separate from Telegram UI code, so the core task/session logic can be tested and extended independently.

## Task Library Model

Task content is stored as JSON. A library can contain multiple modules, and each module can group tasks into units:

```text
src/libraries/<library_id>/
  library.json
  modules/
    <module_id>/
      module.json
      tasks/
        task_001.json
```

Example module grouping:

```json
{
  "group_id": "u1a",
  "title": "Unit 1A - Everyday plans",
  "tasks": ["task_001"]
}
```

This makes it possible to represent textbook-like navigation inside Telegram while keeping the content editable as structured data.

## Local Run

Create `.env` from the example:

```bash
cp .env.example .env
```

Fill in your own Telegram bot token:

```env
BOT_TOKEN=
SCORING_MODE=rule
LLM_API_KEY=
LLM_MODEL=
LLM_BASE_URL=
LIBRARIES_PATH=src/libraries
DATA_PATH=data
LOG_PATH=data/logs/app.log
```

Install dependencies:

```bash
uv sync
```

Run the bot:

```bash
uv run python -m src.app.main
```

## Why This Project Matters

English Helper Bot combines product thinking, educational content design, and backend engineering. It shows how a familiar interface like Telegram can be used to build a practical learning tool with structured content, automated assessment, and persistent learner progress.
