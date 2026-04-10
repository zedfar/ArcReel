"""Fungsi utilitas normalisasi URL."""

from __future__ import annotations

import re


def ensure_openai_base_url(url: str | None) -> str | None:
    """Melengkapi akhiran jalur /v1 secara otomatis untuk API yang kompatibel dengan OpenAI.

    Pengguna mungkin hanya mengisi ``https://api.example.com``, tetapi OpenAI SDK mengharapkan
    ``https://api.example.com/v1``. Fungsi ini secara otomatis menambahkan jalur versi jika tidak ada.
    """
    if not url:
        return url
    stripped = url.strip().rstrip("/")
    if not re.search(r"/v\d+$", stripped):
        stripped += "/v1"
    return stripped


def normalize_base_url(url: str | None) -> str | None:
    """Memastikan base_url diakhiri dengan /.

    http_options.base_url dari Google genai SDK mengharuskan akhiran /,
    jika tidak, penyambungan jalur permintaan akan gagal. Backend Gemini bawaan menggunakan fungsi ini.
    """
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    if not url.endswith("/"):
        url += "/"
    return url


def ensure_google_base_url(url: str | None) -> str | None:
    """Menormalisasi base_url untuk Google genai SDK.

    Google genai SDK secara otomatis menyambungkan ``api_version`` (default ``v1beta``) setelah base_url.
    Jika pengguna salah mengisi ``https://example.com/v1beta``, SDK akan menghasilkan
    ``https://example.com/v1beta/v1beta/models``, yang menyebabkan permintaan gagal.

    Fungsi ini menghapus jalur versi di akhir (seperti ``/v1beta``, ``/v1``) dan memastikan akhiran ``/``.
    """
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    url = url.rstrip("/")
    # Menghapus jalur versi di akhir (/v1, /v1beta, /v1alpha, dll)
    url = re.sub(r"/v\d+\w*$", "", url)
    if not url.endswith("/"):
        url += "/"
    return url
