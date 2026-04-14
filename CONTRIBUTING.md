# Contributing Guide

Thank you for your interest in contributing! We welcome code contributions, bug reports, or new feature suggestions.

## Local Development Environment

```bash
# Requirements: Python 3.12+, Node.js 20+, uv, pnpm, ffmpeg

# Install dependencies
uv sync
cd frontend && pnpm install && cd ..

# Initialize database
uv run alembic upgrade head

# Run backend (Terminal 1)
uv run uvicorn server.app:app --reload --port 1241

# Run frontend (Terminal 2)
cd frontend && pnpm dev

# Access http://localhost:5173
```

## Running Tests

```bash
# Backend Testing
python -m pytest

# Frontend Type Checking + Testing
cd frontend && pnpm check
```

## Code Quality

**Lint & Format (ruff):**

```bash
uv run ruff check . && uv run ruff format .
```

- Rules: `E`/`F`/`I`/`UP`, ignore `E402` and `E501`.
- Line length: 120.
- Mandatory CI checks: `ruff check . && ruff format --check .`.

**Test Coverage:**

- CI requirement ≥ 80%.
- `asyncio_mode = "auto"` (no need to manually mark async tests).

## Commit Message Standards

Commit messages use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
feat: Description of new feature
fix: Description of bug fix
refactor: Description of code refactoring
docs: Documentation changes
chore: Build/tool changes
```

Co-authored use:
- Co-authored-by: Yin <ulfar.far@gmail.com>
- Co-authored-by: Varnimyr AI <varnimyr.ai@gmail.com>
