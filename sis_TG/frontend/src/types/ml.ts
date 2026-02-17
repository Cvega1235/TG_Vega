export interface MLScoreData {
  cluster_id: number;
  cluster_label: string | null;
  icp_similarity: number;
  cluster_score: number;
  composite_score: number;
  calculated_at: string;
}

export interface MLRunInfo {
  id: number;
  optimal_k: number;
  silhouette_score: number;
  davies_bouldin_index: number;
  calinski_harabasz_index: number;
  total_restaurants_scored: number;
  icp_clients_count: number;
  run_at: string;
}

export interface ClusterProfile {
  cluster_id: number;
  label: string | null;
  size: number;
  avg_rating: number | null;
  avg_reviews: number | null;
  dominant_cuisine: string | null;
  dominant_zone: string | null;
  dominant_price: string | null;
  avg_composite_score: number | null;
}

export interface MLRunResult {
  run_metadata: MLRunInfo;
  cluster_profiles: ClusterProfile[];
  message: string;
}

export interface TopProspect {
  id: number;
  nombre: string;
  fuente: string;
  zona: string | null;
  rating: number | null;
  tipo_cocina: string | null;
  precio: string | null;
  cluster_id: number | null;
  icp_similarity: number | null;
  composite_score: number | null;
}
