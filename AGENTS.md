# AGENTS.md

File ini memberikan panduan bagi Codex (Codex.ai/code) saat bekerja dengan kode di repositori ini.

## Standar Bahasa
- **Jawaban kepada pengguna WAJIB menggunakan Bahasa Indonesia**: Semua balasan, daftar tugas, dan file rencana harus menggunakan Bahasa Indonesia.

## Ikhtisar Proyek

ArcReel adalah platform pembuatan video AI yang mengubah novel menjadi video pendek. Arsitektur tiga lapis:

```
frontend/ (React SPA)  →  server/ (FastAPI)  →  lib/ (Pustaka Inti)
  React 19 + Tailwind       Distribusi Rute + SSE  API Gemini
  Rute wouter               agent_runtime/         GenerationQueue
  Manajemen State zustand   (Claude Agent SDK)     ProjectManager
```

## Perintah Pengembangan

```bash
# Backend
uv run python -m pytest                              # Pengujian (-v file tunggal / -k kata kunci / --cov cakupan)
uv run ruff check . && uv run ruff format .          # lint + format
uv sync                                              # Instal dependensi
uv run alembic upgrade head                          # Migrasi database
uv run alembic revision --autogenerate -m "desc"     # Buat migrasi baru

# Frontend (di dalam direktori frontend/)
pnpm build       # Build produksi (termasuk typecheck)
pnpm check       # typecheck + pengujian
```

## Poin Penting Arsitektur

### Rute API Backend

Semua API berada di bawah `/api/v1`, definisi rute ada di `server/routers/`:
- `projects.py` — CRUD Proyek, pembuatan ringkasan.
- `generate.py` — Pembuatan storyboard/video/karakter/petunjuk (masuk ke antrean tugas).
- `assistant.py` — Manajemen sesi Claude Agent SDK (streaming SSE).
- `agent_chat.py` — Interaksi dialog agen cerdas.
- `tasks.py` — Status antrean tugas (streaming SSE).
- `project_events.py` — Push event proyek melalui SSE.
- `files.py` — Unggah file dan aset statis.
- `versions.py` — Riwayat versi aset dan rollback.
- `characters.py` / `clues.py` — Manajemen karakter/petunjuk.
- `usage.py` — Statistik penggunaan API.
- `cost_estimation.py` — Estimasi biaya (proyek/episode/shot).
- `auth.py` / `api_keys.py` — Autentikasi dan manajemen API Key.
- `system_config.py` — Konfigurasi sistem.
- `providers.py` — Manajemen konfigurasi penyedia bawaan (daftar, baca/tulis, tes koneksi).
- `custom_providers.py` — CRUD penyedia kustom, manajemen & deteksi model, tes koneksi.

### server/services/ — Lapisan Layanan Bisnis

- `generation_tasks.py` — Orkestrasi tugas pembuatan storyboard/video/karakter/petunjuk.
- `project_archive.py` — Ekspor proyek (paket ZIP).
- `project_events.py` — Publikasi event perubahan proyek.
- `jianying_draft_service.py` — Ekspor draf Jianying/CapCut.
- `cost_estimation.py` — Perhitungan estimasi biaya dan ringkasan biaya aktual.

### lib/ — Modul Inti

- **{gemini,ark,grok,openai}_shared** — Factory SDK penyedia dan utilitas bersama.
- **image_backends/** / **video_backends/** / **text_backends/** — Backend pembuatan media multi-provider, pola Registry + Factory (gemini/ark/grok/openai).
- **custom_provider/** — Dukungan penyedia kustom: wrapper backend, deteksi model, pembuatan factory (kompatibel OpenAI/Google).
- **MediaGenerator** (`media_generator.py`) — Kombinasi backend + VersionManager + UsageTracker.
- **GenerationQueue** (`generation_queue.py`) — Antrean tugas asinkron, backend SQLAlchemy ORM, kontrol konkurensi berbasis sewa (lease-based).
- **GenerationWorker** (`generation_worker.py`) — Worker latar belakang, dibagi menjadi dua saluran konkurensi: gambar/video.
- **ProjectManager** (`project_manager.py`) — Operasi sistem file proyek dan manajemen data.
- **StatusCalculator** (`status_calculator.py`) — Menghitung field status saat dibaca, tidak menyimpan status redundan.
- **UsageTracker** (`usage_tracker.py`) — Pelacakan penggunaan API.
- **CostCalculator** (`cost_calculator.py`) — Perhitungan biaya.
- **TextGenerator** (`text_generator.py`) — Tugas pembuatan teks.
- **retry** (`retry.py`) — Dekorator percobaan ulang exponential backoff umum, digunakan kembali oleh backend penyedia.

### lib/config/ — Sistem Konfigurasi Penyedia

ConfigService (`service.py`) → Repository (persistensi + desensitisasi kunci) → Resolver (resolusi). `registry.py` memelihara registri penyedia bawaan (PROVIDER_REGISTRY).

### lib/db/ — Lapisan SQLAlchemy Async ORM

- `engine.py` — Mesin asinkron + session factory (`DATABASE_URL` default `sqlite+aiosqlite`).
- `models/` — Model ORM: Task / ApiCall / ApiKey / AgentSession / Config / Credential / User / CustomProvider / CustomProviderModel.
- `repositories/` — Repository asinkron: Task / Usage / Session / ApiKey / Credential / CustomProvider.

File database: `projects/.arcreel.db` (SQLite pengembangan).

### Agent Runtime (Integrasi Claude Agent SDK)

`server/agent_runtime/` membungkus Claude Agent SDK:
- `AssistantService` (`service.py`) — Orkestrasi sesi Claude SDK.
- `SessionManager` — Siklus hidup sesi + pola subscriber SSE.
- `StreamProjector` — Membangun balasan asisten real-time dari event streaming.

### Frontend

- React 19 + TypeScript + Tailwind CSS 4.
- Rute: `wouter` (bukan React Router).
- Manajemen State: `zustand` (store di `frontend/src/stores/`).
- Alias Path: `@/` → `frontend/src/`.
- Proksi Vite: `/api` → `http://127.0.0.1:1241`.

## Pola Desain Utama

### Pelapisan Data

| Tipe Data | Lokasi Penyimpanan | Strategi |
|-----------|--------------------|----------|
| Definisi Karakter/Petunjuk | `project.json` | Single source of truth, hanya referensi nama di skenario |
| Metadata Episode (episode/title/script_file) | `project.json` | Sinkronisasi saat simpan skenario |
| Field Statistik (scenes_count / status / progress) | Tidak disimpan | Injeksi perhitungan saat baca oleh `StatusCalculator` |

### Komunikasi Real-time

- Asisten: `/api/v1/assistant/sessions/{id}/stream` — Balasan streaming SSE.
- Event Proyek: `/api/v1/projects/{name}/events/stream` — Push perubahan proyek melalui SSE.
- Antrean Tugas: Frontend melakukan polling ke `/api/v1/tasks` untuk mendapatkan status.

### Antrean Tugas

Semua tugas pembuatan (storyboard/video/karakter/petunjuk) dimasukkan ke antrean melalui GenerationQueue secara terpadu, diproses secara asinkron oleh GenerationWorker.
`enqueue_and_wait()` di `generation_queue_client.py` membungkus proses masuk antrean + tunggu selesai.

### Model Data Pydantic

`lib/script_models.py` mendefinisikan `NarrationSegment` dan `DramaScene`, digunakan untuk validasi skenario.
`lib/data_validator.py` memvalidasi struktur dan integritas referensi `project.json` dan JSON episode.

## Lingkungan Berjalan Agen

Konfigurasi khusus agen (skills, agents, prompt sistem) berada di direktori `agent_runtime_profile/`, terpisah secara fisik dari `.claude/` saat pengembangan.

### Pemeliharaan Skill

```bash
# Evaluasi tingkat pemicuan (butuh anthropic SDK: uv pip install anthropic)
PYTHONPATH=~/.claude/plugins/cache/claude-plugins-official/skill-creator/*/skills/skill-creator:$PYTHONPATH \
  uv run python -m scripts.run_eval \
  --eval-set <eval-set.json> \
  --skill-path agent_runtime_profile/.claude/skills/<skill-name> \
  --model sonnet --runs-per-query 2 --verbose
```

#### Catatan Penting

- **Sinkronisasi SKILL.md dan Skrip**: Saat memodifikasi skrip skill, SKILL.md harus diperbarui secara bersamaan, dan sebaliknya. Keduanya harus tetap konsisten.

## Konfigurasi Lingkungan

Salin `.env.example` ke `.env`, atur parameter autentikasi (`AUTH_USERNAME`/`AUTH_PASSWORD`/`AUTH_TOKEN_SECRET`).
API Key, pemilihan backend, konfigurasi model, dll. dikelola melalui halaman konfigurasi WebUI (`/settings`).
Dependensi alat eksternal: `ffmpeg` (penggabungan video dan pascaproduksi).

### Kualitas Kode

**ruff** (lint + format):
- Aturan: `E`/`F`/`I`/`UP`, abaikan `E402` (pola yang sudah ada) dan `E501` (dikelola oleh formatter).
- Panjang baris: 120.
- Kecualikan direktori `.worktrees`, `.claude/worktrees`.
- Pemeriksaan wajib di CI: `ruff check . && ruff format --check .`.

**pytest**:
- `asyncio_mode = "auto"` (tidak perlu menandai tes async secara manual).
- Cakupan pengujian: `lib/` dan `server/`, persyaratan CI ≥ 80%.
- Fixture bersama di `tests/conftest.py`, factory di `tests/factories.py`, fakes di `tests/fakes.py`.
- Dependensi tes ada di `[dependency-groups] dev`, diinstal default oleh `uv sync`. Image produksi mengecualikannya melalui `--no-dev`.
