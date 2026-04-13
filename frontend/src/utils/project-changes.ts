import type { ProjectChange } from "@/types";

const GROUP_NAME_LIMIT = 5;

const ENTITY_LABELS: Record<ProjectChange["entity_type"], string> = {
  project: "Dự án",
  character: "Nhân vật",
  clue: "Manh mối",
  segment: "Phân cảnh",
  episode: "Tập",
  overview: "Tổng quan dự án",
  draft: "Tiền xử lý",
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
    return "Ảnh phân cảnh";
  }
  if (group.action === "video_ready") {
    return "Video";
  }
  return ENTITY_LABELS[group.entityType] ?? "Nội dung";
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
  const suffix = group.changes.length > GROUP_NAME_LIMIT ? "…v.v." : "";
  return `${names.join("、")}${suffix}`;
}

function formatSingleNotificationText(change: ProjectChange): string {
  if (change.action === "storyboard_ready") {
    return `Đã tạo ảnh phân cảnh của ${change.label}`;
  }
  if (change.action === "video_ready") {
    return `Đã tạo video của ${change.label}`;
  }
  if (change.action === "created") {
    return `Đã tạo ${change.label}`;
  }
  if (change.action === "deleted") {
    return `Đã xóa ${change.label}`;
  }
  return `Đã cập nhật ${change.label}`;
}

function formatSingleDeferredText(change: ProjectChange): string {
  if (change.action === "storyboard_ready") {
    return `AI vừa tạo ảnh phân cảnh của ${change.label}, nhấn để xem`;
  }
  if (change.action === "video_ready") {
    return `AI vừa tạo video của ${change.label}, nhấn để xem`;
  }
  if (change.action === "created") {
    return `AI vừa thêm ${change.label}, nhấn để xem`;
  }
  if (change.action === "deleted") {
    return `AI vừa xóa ${change.label}, nhấn để xem`;
  }
  return `AI vừa cập nhật ${change.label}, nhấn để xem`;
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
    return `Đã tạo ${count} ${entityLabel}: ${summary}`;
  }
  if (group.action === "created") {
    return `Đã thêm ${count} ${entityLabel}: ${summary}`;
  }
  if (group.action === "deleted") {
    return `Đã xóa ${count} ${entityLabel}: ${summary}`;
  }
  return `Đã cập nhật ${count} ${entityLabel}: ${summary}`;
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
    return `AI vừa tạo ${count} ${entityLabel}: ${summary}, nhấn để xem`;
  }
  if (group.action === "created") {
    return `AI vừa thêm ${count} ${entityLabel}: ${summary}, nhấn để xem`;
  }
  if (group.action === "deleted") {
    return `AI vừa xóa ${count} ${entityLabel}: ${summary}, nhấn để xem`;
  }
  return `AI vừa cập nhật ${count} ${entityLabel}: ${summary}, nhấn để xem`;
}
