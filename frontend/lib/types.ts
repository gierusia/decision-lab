export type User = {
  id: string;
  email: string;
  full_name: string | null;
  created_at: string;
  is_admin?: boolean;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type Workspace = {
  id: string;
  name: string;
  owner_id: string;
  stale_threshold_days: number;
  created_at: string;
};

export type DecisionStatus =
  | "draft"
  | "active"
  | "needs_revision"
  | "completed"
  | "cancelled";

export type Decision = {
  id: string;
  workspace_id: string;
  title: string;
  description: string | null;
  status: DecisionStatus;
  tags: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
};

export type WorkspaceRole = "owner" | "member" | "viewer";

export type Member = {
  id: string;
  user_id: string;
  email: string;
  full_name: string | null;
  role: WorkspaceRole;
  created_at: string;
};

export type DecisionReadiness =
  | "closed"
  | "blocked_by_open_experiments"
  | "draft"
  | "needs_revision"
  | "ready_to_close";

export type DecisionSummary = {
  id: string;
  title: string;
  description: string | null;
  status: DecisionStatus;
  tags: string[];
  author: { id: string; full_name: string | null };
  created_by: string;
  created_at: string;
  updated_at: string;
  is_stale: boolean;
  stale_threshold_days: number;
  stale_after_at: string | null;
  age_seconds: number;
  readiness: DecisionReadiness;
};

export type ExperimentStatus = "planned" | "running" | "completed";
export type ExperimentVerdict = "success" | "partial" | "failed";
export type MetricDirection = "higher_is_better" | "lower_is_better";

export type Experiment = {
  id: string;
  decision_id: string;
  created_by: string;
  status: ExperimentStatus;
  verdict: ExperimentVerdict | null;
  metric_name: string;
  metric_direction: MetricDirection;
  target_value: string;
  actual_value: string | null;
  partial_tolerance_percent: string;
  notes: string | null;
  feature_flag_key: string | null;
  is_frozen: boolean;
};

export type DashboardOut = {
  filters: {
    date_from: string | null;
    date_to: string | null;
    status: DecisionStatus | null;
    author_id: string | null;
    stale_only: boolean;
  };
  pagination: { limit: number; offset: number; total: number };
  totals: {
    decisions: number;
    by_status: Record<DecisionStatus, number>;
    stale: number;
    experiments_open: number;
    experiments_completed: number;
    verdicts: { success: number; partial: number; failed: number };
  };
  decisions: Array<{
    id: string;
    title: string;
    status: DecisionStatus;
    tags: string[];
    author: { id: string; full_name: string | null };
    created_at: string;
    updated_at: string;
    is_stale: boolean;
    readiness: DecisionReadiness;
    experiment_counts: { planned: number; running: number; completed: number };
    verdict_counts: { success: number; partial: number; failed: number };
  }>;
};




