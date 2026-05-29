import apiClient from './client';
import type { DashboardStats, ChartDataPoint, MapDataPoint, TopScoredItem, TopProspect, ClientHistoryData, RecentSummary } from '../types/dashboard';

function fuenteParam(fuente: unknown): Record<string, string> {
  return typeof fuente === 'string' && fuente ? { fuente } : {};
}

export async function getStats(fuente?: string): Promise<DashboardStats> {
  const res = await apiClient.get<DashboardStats>('/dashboard/stats', { params: fuenteParam(fuente) });
  return res.data;
}

export async function getByZone(fuente?: string): Promise<ChartDataPoint[]> {
  const res = await apiClient.get<ChartDataPoint[]>('/dashboard/by-zone', { params: fuenteParam(fuente) });
  return res.data;
}

export async function getByRating(fuente?: string): Promise<ChartDataPoint[]> {
  const res = await apiClient.get<ChartDataPoint[]>('/dashboard/by-rating', { params: fuenteParam(fuente) });
  return res.data;
}

export async function getByCuisine(fuente?: string): Promise<ChartDataPoint[]> {
  const res = await apiClient.get<ChartDataPoint[]>('/dashboard/by-cuisine', { params: fuenteParam(fuente) });
  return res.data;
}

export async function getByStatus(fuente?: string): Promise<ChartDataPoint[]> {
  const res = await apiClient.get<ChartDataPoint[]>('/dashboard/by-status', { params: fuenteParam(fuente) });
  return res.data;
}

export async function getBySource(): Promise<ChartDataPoint[]> {
  const res = await apiClient.get<ChartDataPoint[]>('/dashboard/by-source');
  return res.data;
}

export async function getMapData(): Promise<MapDataPoint[]> {
  const res = await apiClient.get<MapDataPoint[]>('/dashboard/map-data');
  return res.data;
}

export async function getTopScores(limit = 15): Promise<TopScoredItem[]> {
  const res = await apiClient.get<TopScoredItem[]>('/dashboard/top-scores', { params: { limit } });
  return res.data;
}

export async function getTopProspects(limit = 3): Promise<TopProspect[]> {
  const res = await apiClient.get<TopProspect[]>('/dashboard/top-prospects', { params: { limit } });
  return res.data;
}

export async function getClientHistory(): Promise<ClientHistoryData> {
  const res = await apiClient.get<ClientHistoryData>('/dashboard/client-history');
  return res.data;
}

export async function getRecentSummary(days: number): Promise<RecentSummary> {
  const res = await apiClient.get<RecentSummary>('/dashboard/recent-summary', { params: { days } });
  return res.data;
}
