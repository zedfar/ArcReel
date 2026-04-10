/** API Key 元Data（Daftar展示用，不含完整 key）。 */
export interface ApiKeyInfo {
  id: number;
  name: string;
  key_prefix: string;
  created_at: string;
  expires_at: string | null;
  last_used_at: string | null;
}

/** Respons pembuatan API Key (termasuk kunci lengkap, hanya muncul saat dibuat). */
export interface CreateApiKeyResponse {
  id: number;
  name: string;
  key: string;
  key_prefix: string;
  created_at: string;
  expires_at: string | null;
}
