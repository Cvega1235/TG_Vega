import apiClient from './client';
import type { MLRunInfo, MLRunResult, ClusterProfile, TopProspect } from '../types/ml';

export interface RecommendationProspect {
  id: number;
  nombre: string;
  zona: string | null;
  status: string;
  tipo_cocina: string | null;
  rating: number | null;
  composite_score: number;
  conversion_probability: number | null;
}

export interface ZonaOportunidad {
  zona: string;
  total_prospectos: number;
  avg_score: number;
}

export interface SegmentoAfin {
  tipo_cocina: string;
  total: number;
  clientes: number;
  conversion_rate: number;
}

export interface Recommendations {
  acciones_rapidas: RecommendationProspect[];
  top_sin_contactar: RecommendationProspect[];
  zonas_oportunidad: ZonaOportunidad[];
  segmentos_afines: SegmentoAfin[];
}

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

export async function getRecommendations(): Promise<Recommendations> {
  const res = await apiClient.get<Recommendations>('/ml/recommendations');
  return res.data;
}

export interface ScoringWeights {
  w_cuisine: number;
  w_rating: number;
  w_reviews: number;
  w_zone: number;
  w_price: number;
  w_completeness: number;
}

export async function getScoringWeights(): Promise<ScoringWeights> {
  const res = await apiClient.get<ScoringWeights>('/scoring/weights');
  return res.data;
}

export async function updateScoringWeights(weights: ScoringWeights): Promise<ScoringWeights> {
  const res = await apiClient.put<ScoringWeights>('/scoring/weights', weights);
  return res.data;
}
