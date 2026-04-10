import { useState, useRef } from "react";
import { useLocation } from "wouter";
import { X, Loader2, Upload } from "lucide-react";
import { API } from "@/api";
import { useProjectsStore } from "@/stores/projects-store";
import { useAppStore } from "@/stores/app-store";
import { DEFAULT_DURATIONS } from "@/utils/provider-models";

const STYLE_OPTIONS = [
  { value: "Photographic", label: "Fotorealistik" },
  { value: "Anime", label: "Gaya Anime" },
  { value: "3D Animation", label: "Animasi 3D" },
] as const;

export function CreateProjectModal() {
  const [, navigate] = useLocation();
  const { setShowCreateModal, setCreatingProject, creatingProject } =
    useProjectsStore();

  const [title, setTitle] = useState("");
  const [contentMode, setContentMode] = useState<"narration" | "drama">("narration");
  const [aspectRatio, setAspectRatio] = useState<"9:16" | "16:9">("9:16");
  const [style, setStyle] = useState("Photographic");
  const [defaultDuration, setDefaultDuration] = useState<number | null>(null);
  const [titleError, setTitleError] = useState("");
  const [styleImageFile, setStyleImageFile] = useState<File | null>(null);
  const [styleImagePreview, setStyleImagePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleStyleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setStyleImageFile(file);
    // Membuat URL pratinjau
    const url = URL.createObjectURL(file);
    setStyleImagePreview(url);
  };

  const clearStyleImage = () => {
    setStyleImageFile(null);
    if (styleImagePreview) {
      URL.revokeObjectURL(styleImagePreview);
      setStyleImagePreview(null);
    }
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim()) {
      setTitleError("Judul proyek tidak boleh kosong");
      return;
    }

    setCreatingProject(true);
    try {
      const response = await API.createProject(title.trim(), style, contentMode, aspectRatio, defaultDuration);
      const projectName = response.name;

      // Jika pengguna memilih gambar referensi gaya, unggah setelah proyek dibuat
      if (styleImageFile) {
        try {
          await API.uploadStyleImage(projectName, styleImageFile);
        } catch {
          // Kegagalan unggah gambar gaya tidak memblokir pembuatan proyek
          useAppStore.getState().pushToast(
            "Gagal mengunggah gambar referensi gaya, Anda dapat mengunggahnya kembali nanti di pengaturan proyek",
            "warning"
          );
        }
      }

      setShowCreateModal(false);
      navigate(`/app/projects/${projectName}`);
    } catch (err) {
      useAppStore.getState().pushToast(
        `Gagal membuat proyek: ${(err as Error).message}`,
        "error"
      );
    } finally {
      setCreatingProject(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-md rounded-xl border border-gray-700 bg-gray-900 p-6 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-gray-100">Proyek Baru</h2>
          <button
            type="button"
            onClick={() => setShowCreateModal(false)}
            className="rounded p-1 text-gray-400 hover:bg-gray-800 hover:text-gray-200"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">
              Judul Proyek <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                setTitleError("");
              }}
              placeholder="Contoh: Petualangan di Dunia Isekai"
              className="w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-200 placeholder-gray-500 outline-none focus:border-indigo-500"
            />
            {titleError && (
              <p className="mt-1 text-xs text-red-400">{titleError}</p>
            )}
            <p className="mt-1 text-xs text-gray-600">
              Sistem akan otomatis menghasilkan identitas internal proyek untuk URL dan penyimpanan file
            </p>
          </div>

          {/* Content Mode */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">
              Mode Konten
            </label>
            <div className="flex gap-3">
              <label className={`flex-1 cursor-pointer rounded-lg border px-3 py-2 text-center text-sm transition-colors ${
                contentMode === "narration"
                  ? "border-indigo-500 bg-indigo-500/10 text-indigo-300"
                  : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600"
              }`}>
                <input
                  type="radio"
                  name="contentMode"
                  value="narration"
                  checked={contentMode === "narration"}
                  onChange={() => setContentMode("narration")}
                  className="sr-only"
                />
                Narasi + Gambar
              </label>
              <label className={`flex-1 cursor-pointer rounded-lg border px-3 py-2 text-center text-sm transition-colors ${
                contentMode === "drama"
                  ? "border-indigo-500 bg-indigo-500/10 text-indigo-300"
                  : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600"
              }`}>
                <input
                  type="radio"
                  name="contentMode"
                  value="drama"
                  checked={contentMode === "drama"}
                  onChange={() => setContentMode("drama")}
                  className="sr-only"
                />
                Animasi Drama
              </label>
            </div>
          </div>

          {/* Aspect Ratio */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">
              Rasio Aspek
            </label>
            <div className="flex gap-3">
              <label className={`flex-1 cursor-pointer rounded-lg border px-3 py-2 text-center text-sm transition-colors ${
                aspectRatio === "9:16"
                  ? "border-indigo-500 bg-indigo-500/10 text-indigo-300"
                  : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600"
              }`}>
                <input
                  type="radio"
                  name="aspectRatio"
                  value="9:16"
                  checked={aspectRatio === "9:16"}
                  onChange={() => setAspectRatio("9:16")}
                  className="sr-only"
                />
                Vertikal 9:16
              </label>
              <label className={`flex-1 cursor-pointer rounded-lg border px-3 py-2 text-center text-sm transition-colors ${
                aspectRatio === "16:9"
                  ? "border-indigo-500 bg-indigo-500/10 text-indigo-300"
                  : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600"
              }`}>
                <input
                  type="radio"
                  name="aspectRatio"
                  value="16:9"
                  checked={aspectRatio === "16:9"}
                  onChange={() => setAspectRatio("16:9")}
                  className="sr-only"
                />
                Horizontal 16:9
              </label>
            </div>
          </div>

          {/* Default Duration */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-0.5">
              Durasi Default
            </label>
            <p className="text-xs text-gray-600 mb-1.5">
              Durasi ditentukan otomatis oleh AI berdasarkan konten, atau tentukan durasi tetap
            </p>
            <div className="flex gap-2" role="radiogroup" aria-label="Durasi default">
              <button
                type="button"
                role="radio"
                aria-checked={defaultDuration === null}
                onClick={() => setDefaultDuration(null)}
                className={`flex-1 rounded-lg border px-3 py-2 text-sm transition-colors ${
                  defaultDuration === null
                    ? "border-indigo-500 bg-indigo-500/10 text-indigo-300"
                    : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600"
                }`}
              >
                Otomatis
              </button>
              {DEFAULT_DURATIONS.map((d) => (
                <button
                  key={d}
                  type="button"
                  role="radio"
                  aria-checked={defaultDuration === d}
                  onClick={() => setDefaultDuration(d)}
                  className={`flex-1 rounded-lg border px-3 py-2 text-sm transition-colors ${
                    defaultDuration === d
                      ? "border-indigo-500 bg-indigo-500/10 text-indigo-300"
                      : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600"
                  }`}
                >
                  {d}s
                </button>
              ))}
            </div>
          </div>

          {/* Style — fixed radio options */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">
              Gaya Visual
            </label>
            <div className="flex gap-2">
              {STYLE_OPTIONS.map((opt) => (
                <label
                  key={opt.value}
                  className={`flex-1 cursor-pointer rounded-lg border px-3 py-2 text-center text-sm transition-colors ${
                    style === opt.value
                      ? "border-indigo-500 bg-indigo-500/10 text-indigo-300"
                      : "border-gray-700 bg-gray-800 text-gray-400 hover:border-gray-600"
                  }`}
                >
                  <input
                    type="radio"
                    name="style"
                    value={opt.value}
                    checked={style === opt.value}
                    onChange={() => setStyle(opt.value)}
                    className="sr-only"
                  />
                  {opt.label}
                </label>
              ))}
            </div>
          </div>

          {/* Style reference image */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">
              Gambar Referensi Gaya <span className="text-xs text-gray-600 font-normal">(Opsional)</span>
            </label>
            {styleImagePreview ? (
              <div className="relative rounded-lg border border-gray-700 overflow-hidden">
                <img
                  src={styleImagePreview}
                  alt="Pratinjau gambar gaya"
                  className="w-full h-32 object-cover"
                />
                <button
                  type="button"
                  onClick={clearStyleImage}
                  className="absolute top-1.5 right-1.5 rounded-full bg-gray-900/80 p-1 text-gray-300 hover:bg-gray-900 hover:text-white transition-colors"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-gray-700 bg-gray-800/50 px-3 py-4 text-sm text-gray-500 transition-colors hover:border-gray-500 hover:text-gray-300"
              >
                <Upload className="h-4 w-4" />
                Unggah Gambar Referensi
              </button>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept=".png,.jpg,.jpeg,.webp"
              onChange={handleStyleImageChange}
              className="hidden"
            />
            <p className="mt-1 text-xs text-gray-600">
              Karakteristik gaya akan otomatis dianalisis setelah diunggah untuk menghasilkan gambar yang konsisten
            </p>
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={creatingProject || !title.trim()}
            className="w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {creatingProject ? (
              <span className="inline-flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                Membuat...
              </span>
            ) : (
              "Buat Proyek"
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
