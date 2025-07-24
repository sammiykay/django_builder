// API Response Types
export interface AuthResponse {
  access: string;
  refresh: string;
  user: User;
  tokens: {
    access: string;
    refresh: string;
  };
}

export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  date_joined: string;
  is_active: boolean;
}

export interface UserProfile {
  id: string;
  user: User;
  avatar?: string;
  bio?: string;
  location?: string;
  website?: string;
  github_username?: string;
  twitter_username?: string;
  linkedin_username?: string;
  created_at: string;
  updated_at: string;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  user: string;
  created_at: string;
  updated_at: string;
  is_running: boolean;
  container_port?: number;
  container_id?: string;
  ai_generation_status: string;
}

export interface CreateProjectRequest {
  name: string;
  description: string;
}

export interface ProjectFile {
  id: string;
  project: string;
  name: string;
  content: string;
  file_type: string;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  thread: string;
  message: string;
  response: string;
  is_error: boolean;
  created_at: string;
}

export interface CommandExecution {
  id: string;
  project: string;
  command: string;
  output: string;
  error: string;
  exit_code: number;
  executed_at: string;
}

export interface GenerationResponse {
  message: string;
  files_generated: number;
  status: string;
  ai_response?: string;
}

export interface ConversationResponse {
  response: string;
  thread_id: string;
  suggestions?: string[];
  files_modified?: string[];
  commands_executed?: string[];
}

export interface BillingPlan {
  id: number;
  name: string;
  description: string;
  plan_type: 'free' | 'paid' | 'enterprise';
  price: string;
  billing_interval: 'monthly' | 'yearly' | 'one_time';
  token_limit: number;
  bonus_tokens: number;
  max_projects: number;
  max_concurrent_containers: number;

  // Boolean feature flags (replacing advanced_features object)
  enable_ai_chat: boolean;
  enable_auto_error_fix: boolean;
  enable_advanced_templates: boolean;
  enable_custom_containers: boolean;
  enable_code_export: boolean;
  enable_version_control: boolean;
  enable_collaboration: boolean;
  enable_analytics: boolean;
  enable_priority_support: boolean;
  enable_custom_models: boolean;
  enable_api_access: boolean;
  enable_white_labeling: boolean;

  is_active: boolean;
  is_default_free: boolean;
  sort_order: number;
}

export interface UserSubscription {
  id: number;
  user: string;
  plan: BillingPlan;
  status: 'active' | 'cancelled' | 'expired' | 'pending';
  current_period_start: string;
  current_period_end: string;
  tokens_used: number;
  created_at: string;
  updated_at: string;
}

export interface BillingInvoice {
  id: number;
  subscription: number;
  amount: string;
  status: 'pending' | 'paid' | 'failed' | 'cancelled';
  due_date: string;
  paid_at?: string;
  created_at: string;
}