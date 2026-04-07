export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'superadmin' | 'admin' | 'analista' | 'viewer';
  is_active: boolean;
  permissions: string[] | null;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface OTPResponse {
  otp_token: string;
  email: string;
  message: string;
}

export interface VerifyOTPRequest {
  otp_token: string;
  code: string;
}
