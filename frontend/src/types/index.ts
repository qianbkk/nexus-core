export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  role: 'admin' | 'manager' | 'editor' | 'viewer';
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Note {
  id: string;
  title: string;
  content: string;
  excerpt?: string;
  tags: string[];
  notebook_id?: string;
  author_id: string;
  is_public: boolean;
  view_count: number;
  created_at: string;
  updated_at: string;
}

export interface Notebook {
  id: string;
  name: string;
  description?: string;
  color: string;
  icon: string;
  parent_id?: string;
  author_id: string;
  note_count: number;
  created_at: string;
  updated_at: string;
}

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  trigger_type: 'manual' | 'scheduled' | 'webhook' | 'event';
  trigger_config?: Record<string, unknown>;
  steps: WorkflowStep[];
  is_active: boolean;
  author_id: string;
  execution_count: number;
  last_execution_at?: string;
  created_at: string;
  updated_at: string;
}

export interface WorkflowStep {
  id: string;
  workflow_id: string;
  step_number: number;
  action_type: string;
  action_config: Record<string, unknown>;
  condition?: string;
  is_async: boolean;
  timeout_seconds: number;
  retry_count: number;
  created_at: string;
}

export interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  details: Record<string, unknown>;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}

export interface APIError {
  detail: string;
  status_code: number;
}
