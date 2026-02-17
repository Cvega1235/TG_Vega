export interface DashboardStats {
  total_restaurants: number;
  avg_rating: number | null;
  total_with_coordinates: number;
  total_with_phone: number;
  status_counts: Record<string, number>;
  source_counts: Record<string, number>;
}

export interface ChartDataPoint {
  label: string;
  value: number;
}

export interface MapDataPoint {
  id: number;
  nombre: string;
  latitud: number;
  longitud: number;
  rating: number | null;
  status: string;
  total_score: number | null;
}

export interface TopScoredItem {
  id: number;
  nombre: string;
  zona: string | null;
  fuente: string;
  rating: number | null;
  status: string;
  total_score: number;
}
