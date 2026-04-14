import type { ProjectChange } from "@/types";

const GROUP_NAME_LIMIT = 5;

const ENTITY_LABELS: Record<ProjectChange["entity_type"], string> = {
  project: "Project",
  character: "Character",
  clue: "Clue",
  segment: "Storyboard",
  episode: "Episode",
  overview: "Project Overview",
  draft: "Pre-processing",
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
  return ENTITY_LABELS[group.entityType] ?? "Content";
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
  const suffix = group.changes.length > GROUP_NAME_LIMIT ? ", etc." : "";
  return `${names.join(", ")}${suffix}`;
}

function formatSingleNotificationText(change: ProjectChange): string {
  if (change.action === "storyboard_ready") {
    return `${change.label} storyboard has been generated`;
  }
  if (change.action === "video_ready") {
    return `${change.label} video has been generated`;
  }
  if (change.action === "created") {
    return `${change.label} has been created`;
  }
  if (change.action === "deleted") {
    return `${change.label} has been deleted`;
  }
  return `${change.label} has been updated`;
}

function formatSingleDeferredText(change: ProjectChange): string {
  if (change.action === "storyboard_ready") {
    return `AI just generated ${change.label} storyboard. Click to view`;
  }
  if (change.action === "video_ready") {
    return `AI just generated ${change.label} video. Click to view`;
  }
  if (change.action === "created") {
    return `AI just added ${change.label}. Click to view`;
  }
  if (change.action === "deleted") {
    return `AI just deleted ${change.label}. Click to view`;
  }
  return `AI just updated ${change.label}. Click to view`;
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
    return `Generated ${count} ${entityLabel}: ${summary}`;
  }
  if (group.action === "created") {
    return `Added ${count} ${entityLabel}: ${summary}`;
  }
  if (group.action === "deleted") {
    return `Deleted ${count} ${entityLabel}: ${summary}`;
  }
  return `Updated ${count} ${entityLabel}: ${summary}`;
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
    return `AI just generated ${count} ${entityLabel}: ${summary}. Click to view`;
  }
  if (group.action === "created") {
    return `AI just added ${count} ${entityLabel}: ${summary}. Click to view`;
  }
  if (group.action === "deleted") {
    return `AI just deleted ${count} ${entityLabel}: ${summary}. Click to view`;
  }
  return `AI just updated ${count} ${entityLabel}: ${summary}. Click to view`;
}
