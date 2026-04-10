# Panduan Kontribusi

Terima kasih telah tertarik untuk berkontribusi! Kami menerima kontribusi kode, laporan bug, atau saran fitur baru.

## Lingkungan Pengembangan Lokal

```bash
# Persyaratan: Python 3.12+, Node.js 20+, uv, pnpm, ffmpeg

# Instal dependensi
uv sync
cd frontend && pnpm install && cd ..

# Inisialisasi database
uv run alembic upgrade head

# Jalankan backend (Terminal 1)
uv run uvicorn server.app:app --reload --port 1241

# Jalankan frontend (Terminal 2)
cd frontend && pnpm dev

# Akses http://localhost:5173
```

## Menjalankan Pengujian

```bash
# Pengujian Backend
python -m pytest

# Pemeriksaan Tipe Frontend + Pengujian
cd frontend && pnpm check
```

## Kualitas Kode

**Lint & Format (ruff):**

```bash
uv run ruff check . && uv run ruff format .
```

- Aturan: `E`/`F`/`I`/`UP`, abaikan `E402` dan `E501`.
- Panjang baris (line-length): 120.
- Pemeriksaan wajib di CI: `ruff check . && ruff format --check .`.

**Cakupan Pengujian (Test Coverage):**

- Persyaratan CI ≥ 80%.
- `asyncio_mode = "auto"` (tidak perlu menandai tes async secara manual).

## Standar Pesan Komit (Commit)

Pesan komit menggunakan format [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Deskripsi fitur baru
fix: Deskripsi perbaikan masalah
refactor: Deskripsi refaktorisasi kode
docs: Perubahan dokumentasi
chore: Perubahan build/alat bantu
```
