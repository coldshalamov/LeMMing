export interface ScheduleInfo {
  run_every_n_ticks: number;
  phase_offset: number;
}

export interface CreditsInfo {
  model?: string | null;
  credits_left?: number | null;
  max_credits?: number | null;
  soft_cap?: number | null;
  cost_per_action?: number | null;
}

export interface AgentInfo {
  name: string;
  title: string;
  description: string;
  model: string;
  schedule: ScheduleInfo;
  read_outboxes: string[];
  tools: string[];
  credits?: CreditsInfo | null;
}

export interface OrgGraphNode {
  can_read: string[];
  tools: string[];
}

export type OrgGraph = Record<string, OrgGraphNode>;

export interface OrgStatus {
  tick: number;
  total_agents: number;
  total_messages: number;
  total_credits: number;
  timestamp: string;
}

export interface OutboxEntry {
  id: string;
  created_at: string;
  tick: number;
  agent: string;
  kind: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  payload: Record<string, any>;
  tags?: string[] | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  meta?: Record<string, any> | null;
}
