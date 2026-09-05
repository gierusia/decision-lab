import type { ExperimentStatus } from "./types";

const allowed: Record<ExperimentStatus, ExperimentStatus[]> = {
  planned: ["running"],
  running: ["completed"],
  completed: [],
};

export function nextExperimentStatuses(current: ExperimentStatus): ExperimentStatus[] {
  return allowed[current];
}
