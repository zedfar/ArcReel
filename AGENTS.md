# AGENTS.md

This file provides guidance for agents (agent-platforms like OpenClaw) when working with code in this repository.

## Language Standards
- **All responses to users MUST be in English**: All responses, task lists, and plan files should be in English.

## Project Overview

ArcReel is an AI video creation platform that transforms novels into short videos. Three-tier architecture:

```
frontend/ (React SPA)  →  server/ (FastAPI)  →  lib/ (Core Library)
  React 19 + Tailwind       Route Distribution + SSE  Gemini API
  wouter Routes             agent_runtime/         GenerationQueue
  zustand State Management  (Claude Agent SDK)     ProjectManager
```

## Development Commands

```bash
# Backend
uv run python -m pytest                              # Testing (-v single file / -k keyword / --cov coverage)
uv run ruff check . && uv run ruff format .          # lint + format
uv sync                                              # Install dependencies
uv run alembic upgrade head                          # Database migration
uv run alembic revision --autogenerate -m "desc"     # Create new migration

# Frontend (in frontend/ directory)
pnpm build       # Production build (includes typecheck)
pnpm check       # typecheck + testing
```

## Architecture Key Points

### Backend API Routes

All APIs are under `/api/v1`, route definitions in `server/routers/`:
- `projects.py` — Project CRUD, summary generation.
- `generate.py` — Storyboard/video/character/cue generation (enqueued in task queue).
- `assistant.py` — Claude Agent SDK session management (SSE streaming).
- `agent_chat.py` — Smart agent dialogue interaction.
- `tasks.py` — Task queue status (SSE streaming).
- `project_events.py` — Project event push via SSE.
- `files.py` — File upload and static asset.
- `versions.py` — Asset version history and rollback.
- `characters.py` / `clues.py` — Character/cue management.
- `usage.py` — API usage statistics.
- `cost_estimation.py` — Cost estimation (project/episode/shot).
- `auth.py` / `api_keys.py` — Authentication and API Key management.
- `system_config.py` — System configuration.
- `providers.py` — Built-in provider config management (list, read/write, connection test).
- `custom_providers.py` — Custom provider CRUD, model management & detection, connection test.

### server/services/ — Business Service Layer

- `generation_tasks.py` — Orchestration of storyboard/video/character/cue generation tasks.
- `project_archive.py` — Project export (ZIP package).
- `project_events.py` — Project change event publication.
- `jianying_draft_service.py` — Jianying/CapCut draft export.
- `cost_estimation.py` — Cost estimation calculation and actual cost summary.

### lib/ — Core Modules

- **{gemini,ark,grok,openai}_shared** — Provider SDK factory and shared utilities.
- **image_backends/** / **video_backends/** / **text_backends/** — Multi-provider media generation backends, Registry + Factory pattern (gemini/ark/grok/openai).
- **custom_provider/** — Custom provider support: backend wrapper, model detection, factory creation (OpenAI/Google compatible).
- **MediaGenerator** (`media_generator.py`) — Backend + VersionManager + UsageTracker combination.
- **GenerationQueue** (`generation_queue.py`) — Asynchronous task queue, SQLAlchemy ORM backend, lease-based concurrency control.
- **GenerationWorker** (`generation_worker.py`) — Background worker, divided into two concurrency channels: image/video.
- **ProjectManager** (`project_manager.py`) — Project file system operations and data management.
- **StatusCalculator** (`status_calculator.py`) — Compute status fields on read, no redundant status storage.
- **UsageTracker** (`usage_tracker.py`) — API usage tracking.
- **CostCalculator** (`cost_calculator.py`) — Cost calculation.
- **TextGenerator** (`text_generator.py`) — Text generation tasks.
- **retry** (`retry.py`) — Generic exponential backoff retry decorator, reused by provider backends.

### lib/config/ — Provider Configuration System

ConfigService (`service.py`) → Repository (persistence + key desensitization) → Resolver (resolution). `registry.py` maintains built-in provider registry (PROVIDER_REGISTRY).

### lib/db/ — SQLAlchemy Async ORM Layer

- `engine.py` — Async engine + session factory (`DATABASE_URL` default `sqlite+aiosqlite`).
- `models/` — ORM Models: Task / ApiCall / ApiKey / AgentSession / Config / Credential / User / CustomProvider / CustomProviderModel.
- `repositories/` — Async Repositories: Task / Usage / Session / ApiKey / Credential / CustomProvider.

Database file: `projects/.arcreel.db` (SQLite development).

### Agent Runtime (Claude Agent SDK Integration)

`server/agent_runtime/` wraps Claude Agent SDK:
- `AssistantService` (`service.py`) — Claude SDK session orchestration.
- `SessionManager` — Session lifecycle + SSE subscriber pattern.
- `StreamProjector` — Build real-time assistant response from streaming events.

### Frontend

- React 19 + TypeScript + Tailwind CSS 4.
- Routing: `wouter` (not React Router).
- State Management: `zustand` (stores in `frontend/src/stores/`).
- Path Alias: `@/` → `frontend/src/`.
- Vite Proxy: `/api` → `http://127.0.0.1:1241`.

## Main Design Patterns

### Data Layering

| Data Type | Storage Location | Strategy |
|-----------|--------------------|----------|
| Character/Cue Definitions | `project.json` | Single source of truth, only reference names in scenarios |
| Episode Metadata (episode/title/script_file) | `project.json` | Sync when saving scenarios |
| Stat Fields (scenes_count / status / progress) | Not stored | Injected on read by `StatusCalculator` |

### Real-time Communication

- Assistant: `/api/v1/assistant/sessions/{id}/stream` — SSE response streaming.
- Project Events: `/api/v1/projects/{name}/events/stream` — Project changes pushed via SSE.
- Task Queue: Frontend polls `/api/v1/tasks` for status.

### Task Queue

All generation tasks (storyboard/video/character/cue) are enqueued through GenerationQueue unitedly, processed asynchronously by GenerationWorker.
`enqueue_and_wait()` in `generation_queue_client.py` wraps enqueue process + wait completion.

### Pydantic Data Models

`lib/script_models.py` defines `NarrationSegment` and `DramaScene`, used for scenario validation.
`lib/data_validator.py` validates structure and reference integrity of `project.json` and episode JSON.

## Agent Runtime Environment

Agent-specific configuration (skills, agents, system prompts) is in `agent_runtime_profile/` directory, physically separate from `.claude/` during development.

### Skill Maintenance

```bash
# Evaluate trigger rate (requires anthropic SDK: uv pip install anthropic)
PYTHONPATH=~/.claude/plugins/cache/claude-plugins-official/skill-creator/*/skills/skill-creator:$PYTHONPATH \
  uv run python -m scripts.run_eval \
  --eval-set <eval-set.json> \
  --skill-path agent_runtime_profile/.claude/skills/<skill-name> \
  --model sonnet --runs-per-query 2 --verbose
```

#### Important Notes

- **SKILL.md and Script Synchronization**: When modifying skill scripts, SKILL.md must be updated simultaneously, and vice versa. Both must remain consistent.

## Environment Configuration

Copy `.env.example` to `.env`, set authentication parameters (`AUTH_USERNAME`/`AUTH_PASSWORD`/`AUTH_TOKEN_SECRET`).
API Keys, backend selection, model configuration, etc. are managed through WebUI settings page (`/settings`).
External tool dependencies: `ffmpeg` (video merging and post-processing).

### Code Quality

**ruff** (lint + format):
- Rules: `E`/`F`/`I`/`UP`, ignore `E402` (existing pattern) and `E501` (managed by formatter).
- Line length: 120.
- Exclude directories: `.worktrees`, `.claude/worktrees`.
- Mandatory CI checks: `ruff check . && ruff format --check .`.

**pytest**:
- `asyncio_mode = "auto"` (no need to manually mark async tests).
- Test coverage: `lib/` and `server/`, CI requirement ≥ 80%.
- Shared fixtures in `tests/conftest.py`, factories in `tests/factories.py`, fakes in `tests/fakes.py`.
- Test dependencies in `[dependency-groups] dev`, installed by default with `uv sync`. Production image excludes them via `--no-dev`.
