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
    entity_id: "zhang-san",
    label: "Character \"Zhang San\"",
    important: true,
    focus: null,
    ...overrides,
  };
}

describe("project-changes utils", () => {
  it("groups changes by entity_type and action", () => {
    const groups = groupChangesByType([
      makeChange({ entity_id: "zhang-san", label: "Character \"Zhang San\"" }),
      makeChange({ entity_id: "li-si", label: "Character \"Li Si\"" }),
      makeChange({
        entity_type: "clue",
        entity_id: "jade-pendant",
        label: "Clue \"Jade Pendant\"",
      }),
      makeChange({
        entity_type: "character",
        action: "updated",
        entity_id: "wang-wu",
        label: "Character \"Wang Wu\"",
      }),
    ]);

    expect(groups).toHaveLength(3);
    expect(groups[0]).toMatchObject({
      key: "character:created",
      changes: [expect.objectContaining({ entity_id: "zhang-san" }), expect.objectContaining({ entity_id: "li-si" })],
    });
    expect(groups[1].key).toBe("clue:created");
    expect(groups[2].key).toBe("character:updated");
  });

  it("formats grouped notification text and truncates long lists", () => {
    const [singleGroup] = groupChangesByType([
      makeChange({ entity_id: "zhang-san", label: "Character \"Zhang San\"" }),
    ]);
    expect(formatGroupedNotificationText(singleGroup)).toBe("Character \"Zhang San\" has been created");

    const [grouped] = groupChangesByType([
      makeChange({ entity_id: "zhang-san", label: "Character \"Zhang San\"" }),
      makeChange({ entity_id: "li-si", label: "Character \"Li Si\"" }),
      makeChange({ entity_id: "wang-wu", label: "Character \"Wang Wu\"" }),
      makeChange({ entity_id: "zhao-liu", label: "Character \"Zhao Liu\"" }),
      makeChange({ entity_id: "qian-qi", label: "Character \"Qian Qi\"" }),
      makeChange({ entity_id: "sun-ba", label: "Character \"Sun Ba\"" }),
    ]);

    expect(formatGroupedNotificationText(grouped)).toBe(
      "Added 6 characters: zhang-san, li-si, wang-wu, zhao-liu, qian-qi...etc",
    );
    expect(formatGroupedDeferredText(grouped)).toBe(
      "AI just added 6 characters: zhang-san, li-si, wang-wu, zhao-liu, qian-qi...etc. Click to view",
    );
  });
});
