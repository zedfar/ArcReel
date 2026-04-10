// ---------------------------------------------------------------------------
// cn – lightweight className concatenation utility.
// Filters out falsy values and joins the rest with spaces.
// ---------------------------------------------------------------------------

export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

// ---------------------------------------------------------------------------
// getRoleLabel – maps a turn role to a Chinese display label.
// ---------------------------------------------------------------------------

export function getRoleLabel(role: string): string {
  switch (role) {
    case "assistant":
      return "Asisten";
    case "user":
      return "你";
    case "tool":
      return "Alat";
    case "tool_result":
      return "AlatHasil";
    case "skill_content":
      return "Skill";
    case "result":
      return "Selesai";
    case "system":
      return "Sistem";
    case "stream_event":
      return "流式Perbarui";
    case "unknown":
      return "Pesan";
    default:
      return role || "Pesan";
  }
}
