export type User = {
  id: string;
  email: string;
  full_name: string | null;
  created_at: string;
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

