import apiClient from './client';
import type { DashboardStats, ChartDataPoint, MapDataPoint, TopScoredItem, TopProspect } from '../types/dashboard';

export async function getStats(): Promise<DashboardStats> {
  const res = await apiClient.get<DashboardStats>('/dashboard/stats');
  return res.data;
}

export async function getByZone(): Promise<ChartDataPoint[]> {
  const res = await apiClient.get<ChartDataPoint[]>('/dashboard/by-zone');
  return res.data;
}

export async function getByRating(): Promise<ChartDataPoint[]> {
  const res = await apiClient.get<ChartDataPoint[]>('/dashboard/by-rating');
  return res.data;
}

export async function getByCuisine(): Promise<ChartDataPoint[]> {
  const res = await apiClient.get<ChartDataPoint[]>('/dashboard/by-cuisine');
  return res.data;
}

export async function getByStatus(): Promise<ChartDataPoint[]> {
  const res = await apiClient.get<ChartDataPoint[]>('/dashboard/by-status');
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
