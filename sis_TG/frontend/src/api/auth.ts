import apiClient from './client';
import type { LoginRequest, TokenResponse, User } from '../types/auth';

export async function login(data: LoginRequest): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>('/auth/login', data);
  return res.data;
}

export async function getMe(): Promise<User> {
  const res = await apiClient.get<User>('/auth/me');
  return res.data;
}

export async function refreshToken(refresh_token: string): Promise<TokenResponse> {
  const res = await apiClient.post<TokenResponse>('/auth/refresh', { refresh_token });
  return res.data;
}
