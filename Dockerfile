# ============================================================
# Tahap 1: Membangun Frontend
# ============================================================
FROM node:22-slim AS frontend-builder

WORKDIR /build/frontend

# Mengaktifkan corepack dan menyiapkan pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Salin file dependensi terlebih dahulu untuk memanfaatkan cache Docker
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Salin kode sumber frontend dan bangun (build)
COPY frontend/ ./
RUN pnpm build

# ============================================================
# Tahap 2: Image Produksi
# ============================================================
FROM python:3.12-slim AS production

# Instal dependensi sistem
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Instal uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Menonaktifkan buffering output Python untuk memastikan log tampil real-time di Docker logs
ENV PYTHONUNBUFFERED=1

# Salin dependensi dan file metadata paket terlebih dahulu untuk memanfaatkan cache
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --no-dev --no-install-project

# Salin kode aplikasi
COPY lib/ lib/
COPY server/ server/
COPY alembic/ alembic/
COPY alembic.ini ./
COPY scripts/ scripts/
COPY agent_runtime_profile/ agent_runtime_profile/
COPY public/ public/

# Salin hasil build frontend
COPY --from=frontend-builder /build/frontend/dist/ frontend/dist/

# Buat direktori runtime
RUN mkdir -p projects vertex_keys

# Ekspos port
EXPOSE 1241

# Pemeriksaan kesehatan (Healthcheck)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:1241/health || exit 1

# Perintah untuk menjalankan aplikasi
CMD ["uv", "run", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "1241"]
