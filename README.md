<h1 align="center">
  <br>
  <picture>
    <source media="(prefers-color-scheme: light)" srcset="frontend/public/android-chrome-maskable-512x512.png">
    <source media="(prefers-color-scheme: dark)" srcset="frontend/public/android-chrome-512x512.png">
    <img src="frontend/public/android-chrome-maskable-512x512.png" alt="ArcReel Logo" width="128" style="border-radius: 16px;">
  </picture>
  <br>
  ArcReel
  <br>
</h1>

<h4 align="center">Open-source AI Video Generation Workspace — Novel to Short Video, Powered by AI Agents</h4>

<p align="center">
  <a href="#quick-start"><img src="https://img.shields.io/badge/Quick_Start-blue?style=for-the-badge" alt="Quick Start"></a>
  <a href="https://github.com/ArcReel/ArcReel/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-AGPL--3.0-green?style=for-the-badge" alt="License"></a>
  <a href="https://github.com/ArcReel/ArcReel"><img src="https://img.shields.io/github/stars/ArcReel/ArcReel?style=for-the-badge" alt="Stars"></a>
  <a href="https://github.com/ArcReel/ArcReel/pkgs/container/arcreel"><img src="https://img.shields.io/badge/Docker-ghcr.io-blue?style=for-the-badge&logo=docker" alt="Docker"></a>
  <a href="https://github.com/ArcReel/ArcReel/actions/workflows/test.yml"><img src="https://img.shields.io/github/actions/workflow/status/ArcReel/ArcReel/test.yml?style=for-the-badge&label=Tests" alt="Tests"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Claude_Agent_SDK-Anthropic-191919?logo=anthropic&logoColor=white" alt="Claude Agent SDK">
  <img src="https://img.shields.io/badge/Gemini-Image_&_Video_&_Text-886FBF?logo=googlegemini&logoColor=white" alt="Gemini">
  <img src="https://img.shields.io/badge/Volcengine-Image_&_Video_&_Text-FF6A00?logo=bytedance&logoColor=white" alt="Volcengine">
  <img src="https://img.shields.io/badge/Grok-Image_&_Video_&_Text-000000?logo=x&logoColor=white" alt="Grok">
  <img src="https://img.shields.io/badge/OpenAI-Image_&_Video_&_Text-74AA9C?logo=openai&logoColor=white" alt="OpenAI">
</p>

<p align="center">
  <img src="docs/assets/hero-screenshot.png" alt="ArcReel Workstation" width="800">
</p>

---

## Core Capabilities

<table>
<tr>
<td width="20%" align="center">
<h3>🤖 AI Agent Workflow</h3>
Built on <strong>Claude Agent SDK</strong>, orchestrating Skill + focused multi-agent Subagent collaboration, automating the entire production line from script writing to video synthesis.
</td>
<td width="20%" align="center">
<h3>🎨 Multi-Provider Image Generation</h3>
Supports <strong>Gemini</strong>, <strong>Volcengine</strong>, <strong>Grok</strong>, <strong>OpenAI</strong>, and custom providers. Character design ensures role consistency, cue tracking guarantees property/scene continuity across scenes.
</td>
<td width="20%" align="center">
<h3>🎬 Multi-Provider Video Generation</h3>
Supports <strong>Veo 3.1</strong>, <strong>Seedance</strong>, <strong>Grok</strong>, <strong>Sora 2</strong>, and custom providers, switchable at global or project level.
</td>
<td width="20%" align="center">
<h3>⚡ Asynchronous Task Queue</h3>
RPM rate limiting + independent concurrency channels for Image/Video, lease-based scheduling, supports task continuation after interruption.
</td>
<td width="20%" align="center">
<h3>🖥️ Visual Workstation</h3>
Web UI for project management, asset preview, version rollback, real-time SSE task tracking, with built-in AI assistant.
</td>
</tr>
</table>

## Workflow

```mermaid
graph TD
    A["📖 Upload Novel"] --> B["📝 AI Agent Generates Storyboard Script"]
    B --> C["👤 Generate Character Design"]
    B --> D["🔑 Generate Cue Design"]
    C --> E["🖼️ Generate Storyboard Images"]
    D --> E
    E --> F["🎬 Generate Video Fragments"]
    F --> G["🎞️ FFmpeg Synthesizes Final Video"]
    F --> H["📦 Export Jianying/CapCut Draft"]
```

## Quick Start

### Default Installation (SQLite)

```bash
git clone https://github.com/ArcReel/ArcReel.git
cd ArcReel/deploy
cp .env.example .env
docker compose up -d
# Access http://localhost:1241
```

### Production Installation (PostgreSQL)

```bash
cd ArcReel/deploy/production
cp .env.example .env    # Need to set POSTGRES_PASSWORD
docker compose up -d
```

After first run, login with default account (username `admin`, password set in `.env` via `AUTH_PASSWORD`; if not set, it will be auto-generated on first startup and written back to `.env`), then open **Settings Page** (`/settings`) to complete configuration:

1. **ArcReel Agent** — Configure Anthropic API Key (to power the AI assistant), supports Base URL and model customization.
2. **AI Image/Video** — Configure at least one provider API Key (Gemini / Volcengine / Grok / OpenAI), or add a custom provider.

> 📖 For detailed steps, please refer to [Complete Getting Started Guide](docs/getting-started.md)

## Key Features

- **Complete Production Pipeline** — Novel → Script → Character Design → Storyboard Images → Video Fragments → Final Video, one-click orchestration.
- **Multi-Agent Architecture** — Orchestration Skill detects project status and automatically schedules focused Subagents. Each Subagent completes independent tasks and returns summaries.
- **Multi-Provider Support** — Image/Video/Text support Gemini, Volcengine, Grok, and OpenAI, switchable at global or project level.
- **Custom Providers** — Connect to any API compatible with OpenAI / Google (like Ollama, vLLM, third-party agents), automatic model detection, same functionality as built-in providers.
- **Two Content Modes** — Narration mode splits fragments based on reading rhythm, Drama animation mode arranges based on scene/dialogue structure.
- **Progressive Episode Planning** — Human-machine collaboration for cutting long novels: peak detection → Agent cutting point suggestions → user confirmation → physical cuts, on-demand production.
- **Style Reference Images** — Upload style images, AI will automatically analyze and apply them to all image generation to ensure visual consistency across the project.
- **Character Consistency** — AI generates character designs first, all subsequent storyboards and videos will reference these designs.
- **Cue Tracking** — Key properties or scene elements are marked as "Cues" to maintain visual continuity across scenes.
- **Version History** — Each regeneration automatically saves historical versions, supports one-click rollback.
- **Multi-Provider Cost Tracking** — Image/Video/Text all included in cost calculation, billed according to provider strategy, statistics separated by currency.
- **Cost Estimation** — Estimate project/episode/shot costs before generation, with comparison view between estimated and actual costs.
- **Jianying/CapCut Draft Export** — Export per-episode drafts in ZIP format, supports Jianying v5.x / 6+ ([Operation Guide](docs/jianying-export-guide.md)).
- **Project Import/Export** — Entire project packaged for easy backup and migration.

## Provider Support

ArcReel supports multiple built-in and custom providers through unified `ImageBackend` / `VideoBackend` / `TextBackend` protocols:

### Image Providers

| Provider | Available Models | Capabilities | Billing Method |
|----------|----------------|-----------|------------------|
| **Gemini** (Google) | Nano Banana 2, Nano Banana Pro | Text-to-Image, Image-to-Image | By resolution (USD) |
| **Volcengine** (ByteDance) | Seedream 5.0, Seedream 5.0 Lite, Seedream 4.5, Seedream 4.0 | Text-to-Image, Image-to-Image | Per image (CNY) |
| **Grok** (xAI) | Grok Imagine Image, Grok Imagine Image Pro | Text-to-Image, Image-to-Image | Per image (USD) |
| **OpenAI** | GPT Image 1.5, GPT Image 1 Mini | Text-to-Image, Image-to-Image | Per image (USD) |

### Video Providers

| Provider | Available Models | Capabilities | Billing Method |
|----------|----------------|-----------|------------------|
| **Gemini** (Google) | Veo 3.1, Veo 3.1 Fast, Veo 3.1 Lite | Text-to-Video, Image-to-Video, Video Extension | By resolution × duration (USD) |
| **Volcengine** (ByteDance) | Seedance 2.0, Seedance 2.0 Fast, Seedance 1.5 Pro | Text-to-Video, Image-to-Video, Audio, Seed Control | By token usage (CNY) |
| **Grok** (xAI) | Grok Imagine Video | Text-to-Video, Image-to-Video | Per second (USD) |
| **OpenAI** | Sora 2, Sora 2 Pro | Text-to-Video, Image-to-Video | Per second (USD) |

### Text Providers

| Provider | Available Models | Capabilities | Billing Method |
|----------|----------------|-----------|------------------|
| **Gemini** (Google) | Gemini 3.1 Flash, Gemini 3.1 Flash Lite, Gemini 3 Pro | Text Generation, Structured Output, Vision | By token usage (USD) |
| **Volcengine** (ByteDance) | Doubao Seed Series | Text Generation, Structured Output, Vision | By token usage (CNY) |
| **Grok** (xAI) | Grok 4.20, Grok 4.1 Fast | Text Generation, Structured Output, Vision | By token usage (USD) |
| **OpenAI** | GPT-5.4, GPT-5.4 Mini, GPT-5.4 Nano | Text Generation, Structured Output, Vision | By token usage (USD) |

### Custom Providers

Besides built-in providers, you can connect any API that is **OpenAI-compatible** or **Google-compatible**:

- Add custom provider on settings page, enter Base URL and API Key.
- Automatically calls `/v1/models` to discover available models and determine media type by name.
- Same functionality as built-in providers: global/project-level switching, cost tracking, version management.

Provider selection priority: Project-level settings > Global default.

## Community

Scan the QR code to join the Feishu discussion group, get help and latest updates:

<p align="center">
  <img src="docs/assets/feishu-qr.png" alt="Feishu Group QR Code" width="280">
</p>

## AI Assistant Architecture

ArcReel's AI assistant is built on Claude Agent SDK, using **Orchestration Skill + Focused Subagent** multi-agent architecture:

```mermaid
flowchart TD
    User["User Dialog"] --> Main["Main Agent"]
    Main --> MW["manga-workflow<br/>Orchestration Skill"]
    MW -->|"Status Detection"| PJ["Read project.json<br/>+ File System"]
    MW -->|"dispatch"| SA1["analyze-characters-clues<br/>Extract Global Characters/Cues"]
    MW -->|"dispatch"| SA2["split-narration-segments<br/>Split Narration Mode Fragments"]
    MW -->|"dispatch"| SA3["normalize-drama-script<br/>Normalize Drama Script"]
    MW -->|"dispatch"| SA4["create-episode-script<br/>Create Script JSON"]
    MW -->|"dispatch"| SA5["Asset Generation Subagent<br/>Character/Cue/Storyboard/Video"]
    SA1 -->|"Summary"| Main
    SA4 -->|"Summary"| Main
    Main -->|"Display Results<br/>Await Confirmation"| User
```

**Core Design Principles**:

- **Orchestration Skill (manga-workflow)** — Has status detection capability, automatically determines current project stage and schedules appropriate Subagents.
- **Focused Subagent** — Each Subagent completes only one task. Large context like novel text remains within Subagent, Main Agent receives only brief summaries to conserve context space.
- **Skill vs Subagent Boundary** — Skill responsible for deterministic script execution (API calls, file creation), Subagent responsible for tasks requiring reasoning and analysis.
- **Cross-Stage Confirmation** — After each Subagent returns, Main Agent displays result summary to user and waits for confirmation before proceeding to next stage.

## OpenClaw Integration

ArcReel supports invocation through external AI Agent platforms like [OpenClaw](https://openclaw.ai), enabling video creation through natural language:

1. Generate API Key in ArcReel settings (prefix `arc-`).
2. Load ArcReel Skill definition in OpenClaw (access `http://your-domain/skill.md`).
3. You can create projects, generate scripts, and create videos through dialogue in OpenClaw.

Technical implementation: API Key authentication (Bearer Token) + Synchronous Agent dialog endpoint (`POST /api/v1/agent/chat`).

## Technical Architecture

```mermaid
flowchart TB
    subgraph UI["Web UI — React 19"]
        U1["Project Management"] ~~~ U2["Asset Preview"] ~~~ U3["AI Assistant"] ~~~ U4["Task Monitoring"]
    end

    subgraph Server["FastAPI Server"]
        S1["REST API<br/>Route Distribution"] ~~~ S2["Agent Runtime<br/>Claude Agent SDK"]
        S3["SSE Stream<br/>Real-time Status Push"] ~~~ S4["Auth<br/>JWT + API Key"]
    end

    subgraph Core["Core Library"]
        C1["VideoBackend Abstraction<br/>Gemini · Volcengine · Grok · OpenAI · Custom"] ~~~ C2["ImageBackend Abstraction<br/>Gemini · Volcengine · Grok · OpenAI · Custom"]
        C5["TextBackend Abstraction<br/>Gemini · Volcengine · Grok · OpenAI · Custom"] ~~~ C3["GenerationQueue<br/>RPM Limit · Image/Video Channels"]
        C4["ProjectManager<br/>File System + Version Management"]
    end

    subgraph Data["Data Layer"]
        D1["SQLAlchemy 2.0 Async ORM"] ~~~ D2["SQLite / PostgreSQL"]
        D3["Alembic Migration"] ~~~ D4["UsageTracker<br/>Multi-Provider Cost Tracking"]
    end

    UI --> Server --> Core --> Data
```

## Technology Stack

| Layer | Technology |
|------|------|
| **Frontend** | React 19, TypeScript, Tailwind CSS 4, wouter, zustand, Framer Motion, Vite |
| **Backend** | FastAPI, Python 3.12+, uvicorn, Pydantic 2 |
| **AI Agent** | Claude Agent SDK (Orchestration Skill + Subagent Architecture) |
| **Image Generation** | Gemini (`google-genai`), Volcengine (`volcengine-python-sdk[ark]`), Grok (`xai-sdk`), OpenAI (`openai`) |
| **Video Generation** | Gemini Veo 3.1 (`google-genai`), Volcengine Seedance 2.0/1.5 (`volcengine-python-sdk[ark]`), Grok (`xai-sdk`), OpenAI Sora 2 (`openai`) |
| **Text Generation** | Gemini (`google-genai`), Volcengine (`volcengine-python-sdk[ark]`), Grok (`xai-sdk`), OpenAI (`openai`), Instructor (Fallback structured output) |
| **Media Processing** | FFmpeg, Pillow |
| **ORM & Database** | SQLAlchemy 2.0 (async), Alembic, aiosqlite, asyncpg — SQLite (Default) / PostgreSQL (Production) |
| **Authentication** | JWT (`pyjwt`), API Key (SHA-256 Hash), Password Hash Argon2 (`pwdlib`) |
| **Deployment** | Docker, Docker Compose (`deploy/` default, `deploy/production/` with PostgreSQL) |

## Documentation

- 📖 [Complete Getting Started Guide](docs/getting-started.md) — Step-by-step guide from scratch.
- 📦 [Jianying Draft Export Guide](docs/jianying-export-guide.md) — Import video fragments into Jianying/CapCut Desktop.
- 💰 [Google GenAI Cost Reference](docs/google-genai-docs/Google_video_image_generation_cost_reference.md) — Gemini image / Veo video cost reference.
- 💰 [Volcengine Cost Reference](docs/ark-docs/Volcengine_cost_reference.md) — Volcengine video / image / text model cost reference.

## Contributing

We welcome code contributions, bug reports, or feature suggestions! Please refer to [Contributing Guide](CONTRIBUTING.md) for information about setting up local development environment, testing, and code standards.

## License

[AGPL-3.0](LICENSE)

---

<p align="center">
  If this project is helpful to you, please give us a Star to support us!
</p>
