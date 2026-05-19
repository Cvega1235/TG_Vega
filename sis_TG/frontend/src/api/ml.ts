import apiClient from './client';
import type { MLRunInfo, MLRunResult, ClusterProfile, TopProspect } from '../types/ml';

export async function runMLPipeline(): Promise<MLRunResult> {
  const res = await apiClient.post<MLRunResult>('/ml/run');
  return res.data;
}

export async function getLatestRun(): Promise<MLRunInfo | null> {
  const res = await apiClient.get<MLRunInfo | null>('/ml/latest-run');
  return res.data;
}

export async function getClusterProfiles(): Promise<ClusterProfile[]> {
  const res = await apiClient.get<ClusterProfile[]>('/ml/clusters');
  return res.data;
}

export async function getTopProspects(limit = 20, includeClients = false): Promise<TopProspect[]> {
  const res = await apiClient.get<TopProspect[]>('/ml/top-prospects', {
    params: { limit, include_clients: includeClients },
  });
  return res.data;
}
