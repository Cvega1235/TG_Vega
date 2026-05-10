export interface AuditLog {
  id: number;
  user_id: string | null;
  user_email: string | null;
  action: string;
  resource: string | null;
  resource_id: string | null;
  details: string | null;
  status: 'success' | 'failure' | 'warning';
  ip_address: string | null;
  created_at: string;
}

export interface SecurityStats {
  total_logs: number;
  failed_logins_today: number;
  locked_accounts: number;
  active_alerts: number;
}

export interface SecurityAlert {
  type: 'brute_force' | 'locked_account' | 'suspicious_ip';
  severity: 'high' | 'medium' | 'low';
  description: string;
  ip_address: string | null;
  user_email: string | null;
  count: number;
  last_seen: string;
}
