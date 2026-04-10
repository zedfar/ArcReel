// main.tsx — Titik masuk baru menggunakan wouter + StudioLayout
// Menggantikan main.js sebagai titik masuk aplikasi.
// main.js lama dipertahankan sebagai referensi selama migrasi.

import { createRoot } from "react-dom/client";
import { AppRoutes } from "./router";
import { useAuthStore } from "@/stores/auth-store";

import "./index.css";
import "./css/styles.css";
import "./css/app.css";
import "./css/studio.css";

// Memulihkan status login dari localStorage
useAuthStore.getState().initialize();

// ---------------------------------------------------------------------------
// Auto-hide scrollbar global: muncul saat scroll, menghilang setelah berhenti 1.2 detik
// ---------------------------------------------------------------------------
{
  const timers = new WeakMap<Element, ReturnType<typeof setTimeout>>();

  document.addEventListener(
    "scroll",
    (e) => {
      const el = e.target;
      if (!(el instanceof HTMLElement)) return;

      // Menampilkan scrollbar
      el.dataset.scrolling = "";

      // Menghapus timer sembunyi sebelumnya
      const prev = timers.get(el);
      if (prev) clearTimeout(prev);

      // Sembunyikan setelah 1.2 detik tanpa scroll
      timers.set(
        el,
        setTimeout(() => {
          delete el.dataset.scrolling;
          timers.delete(el);
        }, 1200),
      );
    },
    true, // capture phase — menangkap event scroll dari semua elemen anak
  );
}

const root = document.getElementById("app-root");
if (root) {
  createRoot(root).render(<AppRoutes />);
}
