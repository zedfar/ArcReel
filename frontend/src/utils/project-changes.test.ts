import { describe, expect, it } from "vitest";
import type { ProjectChange } from "@/types";
import {
  formatGroupedDeferredText,
  formatGroupedNotificationText,
  groupChangesByType,
} from "./project-changes";

function makeChange(overrides: Partial<ProjectChange> = {}): ProjectChange {
  return {
    entity_type: "character",
    action: "created",
    entity_id: "张三",
    label: "Karakter \"Zhang San\"",
    important: true,
    focus: null,
    ...overrides,
  };
}

describe("project-changes utils", () => {
  it("groups changes by entity_type and action", () => {
    const groups = groupChangesByType([
      makeChange({ entity_id: "张三", label: "Karakter \"Zhang San\"" }),
      makeChange({ entity_id: "李四", label: "Karakter \"Li Si\"" }),
      makeChange({
        entity_type: "clue",
        entity_id: "玉佩",
        label: "Petunjuk \"Jade Pendant\"",
      }),
      makeChange({
        entity_type: "character",
        action: "updated",
        entity_id: "王五",
        label: "Karakter \"Wang Wu\"",
      }),
    ]);

    expect(groups).toHaveLength(3);
    expect(groups[0]).toMatchObject({
      key: "character:created",
      changes: [expect.objectContaining({ entity_id: "张三" }), expect.objectContaining({ entity_id: "李四" })],
    });
    expect(groups[1].key).toBe("clue:created");
    expect(groups[2].key).toBe("character:updated");
  });

  it("formats grouped notification text and truncates long lists", () => {
    const [singleGroup] = groupChangesByType([
      makeChange({ entity_id: "张三", label: "Karakter \"Zhang San\"" }),
    ]);
    expect(formatGroupedNotificationText(singleGroup)).toBe("Karakter \"Zhang San\"Telah dibuat");

    const [grouped] = groupChangesByType([
      makeChange({ entity_id: "张三", label: "Karakter \"Zhang San\"" }),
      makeChange({ entity_id: "李四", label: "Karakter \"Li Si\"" }),
      makeChange({ entity_id: "王五", label: "Karakter \"Wang Wu\"" }),
      makeChange({ entity_id: "赵六", label: "Karakter \"Zhao Liu\"" }),
      makeChange({ entity_id: "钱七", label: "Karakter \"Qian Qi\"" }),
      makeChange({ entity_id: "孙八", label: "Karakter \"Sun Ba\"" }),
    ]);

    expect(formatGroupedNotificationText(grouped)).toBe(
      "Tambah了 6  karakter：张三、李四、王五、赵六、钱七…等",
    );
    expect(formatGroupedDeferredText(grouped)).toBe(
      "AI baru saja menambahkan 6  karakter：张三、李四、王五、赵六、钱七…等，Klik untuk melihat",
    );
  });
});
