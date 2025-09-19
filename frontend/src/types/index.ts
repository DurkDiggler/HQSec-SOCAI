// Base types for the SOC Agent frontend

// API Response types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  success: boolean;
  timestamp: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  pagination: {
    skip: number;
    limit: number;
    total: number;
    has_more: boolean;
  };
}

// Alert types
export interface Alert {
  id: number;
  source: string | null;
  event_type: string | null;
  severity: number;
  timestamp: string;
  message: string | null;
  ip: string | null;
  username: string | null;
  category: string | null;
  recommended_action: string | null;
  base_score: number;
  intel_score: number;
  final_score: number;
  iocs: Record<string, any>;
  intel_data: Record<string, any>;
  status: string;
  assigned_to: string | null;
  notes: string | null;
  email_sent: boolean;
  ticket_created: boolean;
  ticket_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface AlertFilters {
  skip?: number;
  limit?: number;
  status?: string;
  severity?: number;
  source?: string;
  category?: string;
  search?: string;
}

// Statistics types
export interface Statistics {
  total_alerts: number;
  high_severity: number;
  medium_severity: number;
  low_severity: number;
  resolved_alerts: number;
  false_positives: number;
  avg_response_time: number;
  top_sources: Array<{ source: string; count: number }>;
  top_event_types: Array<{ event_type: string; count: number }>;
  top_ips: Array<{ ip: string; count: number }>;
  alerts_by_hour: Array<{ hour: number; count: number }>;
  alerts_by_day: Array<{ day: string; count: number }>;
}

// User and Authentication types
export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  is_active: boolean;
  last_login: string | null;
  created_at: string;
  updated_at: string;
  roles: Role[];
}

export interface Role {
  id: number;
  name: string;
  display_name: string;
  description: string | null;
  permissions: string[];
  is_system_role: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// AI Analysis types
export interface AIAnalysis {
  id: number;
  alert_id: number;
  analysis_type: string;
  risk_level: string;
  confidence: number;
  summary: string;
  details: Record<string, any>;
  recommendations: string[];
  model_used: string;
  processing_time: number;
  created_at: string;
  updated_at: string;
}

// MCP Server types
export interface MCPServer {
  id: string;
  name: string;
  url: string;
  status: 'available' | 'unavailable' | 'error';
  capabilities: string[];
  last_checked: string;
}

export interface MCPScanResult {
  test_id: number;
  scan_result: Record<string, any>;
  target: string;
  scan_type: string;
  timestamp: string;
}

// Settings types
export interface Settings {
  app_host: string;
  app_port: number;
  log_level: string;
  log_format: string;
  max_request_size: number;
  rate_limit_requests: number;
  rate_limit_window: number;
  cors_origins: string[];
  enable_email: boolean;
  enable_autotask: boolean;
  enable_metrics: boolean;
  enable_caching: boolean;
  enable_realtime: boolean;
  oauth_enabled: boolean;
  oauth_provider: string;
  mfa_enabled: boolean;
  rbac_enabled: boolean;
  ml_enabled: boolean;
  anomaly_detection_enabled: boolean;
  risk_scoring_enabled: boolean;
  classification_enabled: boolean;
  fp_reduction_enabled: boolean;
  pattern_recognition_enabled: boolean;
}

// Real-time types
export interface RealtimeAlert {
  id: number;
  source: string;
  event_type: string;
  severity: number;
  message: string;
  timestamp: string;
  category: string;
  iocs: Record<string, any>;
  scores: {
    base: number;
    intel: number;
    final: number;
  };
  recommended_action: string;
  status: string;
}

export interface RealtimeNotification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

// Chart and visualization types
export interface ChartData {
  name: string;
  value: number;
  color?: string;
}

export interface TimeSeriesData {
  timestamp: string;
  value: number;
  label?: string;
}

// Form types
export interface LoginForm {
  email: string;
  password: string;
  remember?: boolean;
}

export interface RegisterForm {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  firstName?: string;
  lastName?: string;
}

// Error types
export interface ApiError {
  message: string;
  status: number;
  code?: string;
  details?: Record<string, any>;
}

// Component props types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

export interface LoadingProps extends BaseComponentProps {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}

export interface ButtonProps extends BaseComponentProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
  type?: 'button' | 'submit' | 'reset';
}

export interface ModalProps extends BaseComponentProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

// Utility types
export type Status = 'idle' | 'loading' | 'success' | 'error';

export type Severity = 'low' | 'medium' | 'high' | 'critical';

export type Theme = 'light' | 'dark' | 'system';

export type SortOrder = 'asc' | 'desc';

export type SortField = 'timestamp' | 'severity' | 'source' | 'status';

// Generic types
export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};
