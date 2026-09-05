import type { DecisionStatus } from "./types";

const allowed: Record<DecisionStatus, DecisionStatus[]> = {
  draft: ["active", "cancelled"],
  active: ["needs_revision", "completed", "cancelled"],
  needs_revision: ["active", "cancelled"],
  completed: [],
  cancelled: [],
};

export function nextStatuses(current: DecisionStatus): DecisionStatus[] {
  return allowed[current];
}

export function canCloseDecision(
  target: DecisionStatus,
  readiness: string,
  role: string | null,
): boolean {
  if (target !== "completed" && target !== "cancelled") return true;
  if (readiness !== "blocked_by_open_experiments") return true;
  return role === "owner";
}
