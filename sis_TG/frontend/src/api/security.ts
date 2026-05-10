import axios from './client';
import type { AuditLog, SecurityStats, SecurityAlert } from '../types/security';

export const getSecurityStats = async (): Promise<SecurityStats> => {
  const { data } = await axios.get('/security/stats');
  return data;
};

export const getAuditLogs = async (params?: {
  limit?: number;
  offset?: number;
  action?: string;
  status?: string;
  user_email?: string;
}): Promise<AuditLog[]> => {
  const { data } = await axios.get('/security/logs', { params });
  return data;
};

export const getSecurityAlerts = async (): Promise<SecurityAlert[]> => {
  const { data } = await axios.get('/security/alerts');
  return data;
};

export const unlockUser = async (userId: string): Promise<{ message: string }> => {
  const { data } = await axios.post(`/security/users/${userId}/unlock`);
  return data;
};

export const encryptExistingData = async (): Promise<{ message: string }> => {
  const { data } = await axios.post('/security/encrypt-existing');
  return data;
};

export const getEncryptionStatus = async (): Promise<{
  encryption_active: boolean;
  message: string;
}> => {
  const { data } = await axios.get('/security/encryption-status');
  return data;
};
