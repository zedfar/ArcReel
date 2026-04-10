import { useEffect } from "react";

/**
 * 当有未SimpanPerubahan时，阻止用户Tutup/SegarkanTab。
 */
export function useWarnUnsaved(isDirty: boolean) {
  useEffect(() => {
    if (!isDirty) return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isDirty]);
}
