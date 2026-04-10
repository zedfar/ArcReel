import type { ProjectChange } from "@/types";

const GROUP_NAME_LIMIT = 5;

const ENTITY_LABELS: Record<ProjectChange["entity_type"], string> = {
  project: "Proyek",
  character: "Karakter",
  clue: "Petunjuk",
  segment: "Storyboard",
  episode: "Episode",
  overview: "Ikhtisar Proyek",
  draft: "Pra-pemrosesan",
};

export interface GroupedProjectChange {
  key: string;
  entityType: ProjectChange["entity_type"];
  action: ProjectChange["action"];
  changes: ProjectChange[];
}

export function buildEntityRevisionKey(
  entityType: ProjectChange["entity_type"],
  entityId: string,
): string {
  return `${entityType}:${entityId}`;
}

export function buildVersionResourceRevisionKey(
  resourceType: "storyboards" | "videos" | "characters" | "clues",
  resourceId: string,
): string {
  if (resourceType === "storyboards" || resourceType === "videos") {
    return buildEntityRevisionKey("segment", resourceId);
  }
  if (resourceType === "characters") {
    return buildEntityRevisionKey("character", resourceId);
  }
  return buildEntityRevisionKey("clue", resourceId);
}

export function groupChangesByType(
  changes: ProjectChange[],
): GroupedProjectChange[] {
  const groups = new Map<string, GroupedProjectChange>();

  for (const change of changes) {
    const key = `${change.entity_type}:${change.action}`;
    const existing = groups.get(key);
    if (existing) {
      existing.changes.push(change);
      continue;
    }
    groups.set(key, {
      key,
      entityType: change.entity_type,
      action: change.action,
      changes: [change],
    });
  }

  return [...groups.values()];
}

function getEntityLabel(group: GroupedProjectChange): string {
  if (group.action === "storyboard_ready") {
    return "Storyboard";
  }
  if (group.action === "video_ready") {
    return "Video";
  }
  return ENTITY_LABELS[group.entityType] ?? "Konten";
}

function getChangeListLabel(change: ProjectChange): string {
  if (
    change.entity_type === "character" ||
    change.entity_type === "clue" ||
    change.entity_type === "segment"
  ) {
    return change.entity_id;
  }
  return change.label;
}

function summarizeGroupNames(group: GroupedProjectChange): string {
  const names = group.changes.slice(0, GROUP_NAME_LIMIT).map(getChangeListLabel);
  const suffix = group.changes.length > GROUP_NAME_LIMIT ? "…等" : "";
  return `${names.join("、")}${suffix}`;
}

function formatSingleNotificationText(change: ProjectChange): string {
  if (change.action === "storyboard_ready") {
    return `${change.label} storyboard telah dihasilkan`;
  }
  if (change.action === "video_ready") {
    return `${change.label} video telah dihasilkan`;
  }
  if (change.action === "created") {
    return `${change.label}Telah dibuat`;
  }
  if (change.action === "deleted") {
    return `${change.label}Telah dihapus`;
  }
  return `${change.label}Telah diperbarui`;
}

function formatSingleDeferredText(change: ProjectChange): string {
  if (change.action === "storyboard_ready") {
    return `AI baru saja menghasilkan ${change.label}  storyboard，Klik untuk melihat`;
  }
  if (change.action === "video_ready") {
    return `AI baru saja menghasilkan ${change.label}  video，Klik untuk melihat`;
  }
  if (change.action === "created") {
    return `AI baru saja menambahkan ${change.label}，Klik untuk melihat`;
  }
  if (change.action === "deleted") {
    return `AI baru saja menghapus ${change.label}，Klik untuk melihat`;
  }
  return `AI baru saja memperbarui ${change.label}，Klik untuk melihat`;
}

export function formatGroupedNotificationText(
  group: GroupedProjectChange,
): string {
  if (group.changes.length === 1) {
    return formatSingleNotificationText(group.changes[0]);
  }

  const count = group.changes.length;
  const entityLabel = getEntityLabel(group);
  const summary = summarizeGroupNames(group);

  if (group.action === "storyboard_ready" || group.action === "video_ready") {
    return `Telah dihasilkan ${count} ${entityLabel}：${summary}`;
  }
  if (group.action === "created") {
    return `Ditambahkan ${count} ${entityLabel}：${summary}`;
  }
  if (group.action === "deleted") {
    return `Dihapus ${count} ${entityLabel}：${summary}`;
  }
  return `Diperbarui ${count} ${entityLabel}：${summary}`;
}

export function formatGroupedDeferredText(
  group: GroupedProjectChange,
): string {
  if (group.changes.length === 1) {
    return formatSingleDeferredText(group.changes[0]);
  }

  const count = group.changes.length;
  const entityLabel = getEntityLabel(group);
  const summary = summarizeGroupNames(group);

  if (group.action === "storyboard_ready" || group.action === "video_ready") {
    return `AI baru saja menghasilkan ${count} 个${entityLabel}：${summary}，Klik untuk melihat`;
  }
  if (group.action === "created") {
    return `AI 刚Ditambahkan ${count} ${entityLabel}：${summary}，Klik untuk melihat`;
  }
  if (group.action === "deleted") {
    return `AI 刚Dihapus ${count} ${entityLabel}：${summary}，Klik untuk melihat`;
  }
  return `AI 刚Diperbarui ${count} ${entityLabel}：${summary}，Klik untuk melihat`;
}
